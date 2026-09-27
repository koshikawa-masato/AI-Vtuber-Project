"""Synthetic local-Lev privacy smoke test; external search is intercepted."""

import asyncio
import ast
import dataclasses
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['JEV_PROVIDER'] = 'lev'
os.environ['XAI_API_KEY'] = 'dry-run-not-a-real-key'
for name in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY'):
    os.environ.pop(name, None)

from src.core.jev_client import JevClient, JevError
from src.line_bot_vps import fact_check_pipeline as facts
from src.line_bot_vps import privacy_guard as guard


def network_guard(event, args):
    if event == 'socket.connect' and args[1] != ('127.0.0.1', 18009):
        raise RuntimeError('dry_run_external_network_denied')


sys.addaudithook(network_guard)
report = {'cases': [], 'external_requests_sent': 0, 'model_calls': []}
active_case = ''
original_evaluate = JevClient.evaluate_noul


def record_evaluation(self, state, questions):
    assert self.provider == 'lev'
    started = time.perf_counter()
    result = original_evaluate(self, state, questions)
    report['model_calls'].append({'case': active_case, 'probabilities': result.probabilities,
                                  'elapsed_ms': (time.perf_counter() - started) * 1000})
    return result


def save_case(name, expected, action):
    global active_case
    active_case = name
    started = time.perf_counter()
    actual = action()
    row = {'name': name, 'expected': expected, 'actual': actual, 'matches': actual == expected,
           'elapsed_ms': (time.perf_counter() - started) * 1000}
    report['cases'].append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)


def incoming(text):
    result = guard.screen(text)
    return 'hold' if result.review_required else 'block' if result.blocked else 'allow'


def outbound(question):
    sent = []
    def intercept(url, **kwargs):
        sent.append(kwargs['json'])
        return SimpleNamespace(status_code=200, json=lambda: {'output_text': 'dry-run-intercepted'})
    with patch.object(facts.requests, 'post', side_effect=intercept):
        result = facts.ask_grok_with_search(question)
    return {'would_send': len(sent), 'result': result}


class FixedJudge:
    def __init__(self, probability=None):
        self.probability = probability

    def evaluate_noul(self, state, questions):
        if self.probability is None:
            raise JevError('timeout')
        return SimpleNamespace(probabilities={'sensitive': self.probability})


with patch.object(JevClient, 'evaluate_noul', record_evaluation):
    for name, text, expected in [
        ('input_phone', '電話は090-1234-5678です', 'block'),
        ('input_fullwidth_email', '連絡先はｔｅｓｔ＠ｅｘａｍｐｌｅ．ｃｏｍです', 'block'),
        ('input_health', '私はうつ病と診断されて通院しています。', 'block'),
        ('input_fiction', '病院が舞台の架空のドラマが好きです。', 'allow'),
        ('input_clean', '今日のお昼なに食べようかな', 'allow'),
    ]:
        save_case(name, expected, lambda text=text: incoming(text))
    for name, question, expected in [
        ('exit_public_fact', '東京タワーの高さは333メートルです。公式情報で確認してください。', True),
        ('exit_history_phone', '東京タワーを調べて。参考履歴：私の電話は090-1234-5678です。', False),
        ('exit_history_finance', '参考履歴：私の年収は420万円、借金は200万円です。この話を検索してください。', False),
    ]:
        save_case(name, {'would_send': int(expected), 'result': 'dry-run-intercepted' if expected else None},
                  lambda question=question: outbound(question))

for name, judge in [('uncertain', FixedJudge(0.4)), ('unavailable', FixedJudge())]:
    result = guard.screen('病院について', judge)
    save_case('input_' + name, {'blocked': True, 'review': True, 'kinds': []},
              lambda result=result: {'blocked': result.blocked, 'review': result.review_required, 'kinds': result.kinds})
    with patch.object(facts, 'screen_outbound', side_effect=lambda payload, judge=judge: guard.screen_outbound(payload, judge)):
        save_case('exit_' + name, {'would_send': 0, 'result': None}, lambda: outbound('公開情報を検索してください'))

source = Path('/root/AI-Vtuber-Project/src/line_bot_vps/webhook_server_vps.py')
if source.is_file():
    tree = ast.parse(source.read_text())
    function = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'gate_incoming_message')
    branch = next(index for index, node in enumerate(function.body)
                  if isinstance(node, ast.If) and ast.unparse(node.test) == 'result.blocked')
    hold_branch = ast.parse('''if result.review_required:
    send_system_message(user_id, "安全性を確認できないため、処理を保留しました。")
    return True
''').body[0]
    function.body.insert(branch, hold_branch)
    function_source = ast.unparse(function)
    Path('production-gate-reviewed.py').write_text(function_source + '\n')
    def no_incident(*args):
        raise AssertionError('A hold must not record a privacy incident')
    namespace = {'asyncio': asyncio, 'privacy_connection': lambda: None,
                 'privacy_guard': SimpleNamespace(banned_until=lambda *args: None,
                     screen=lambda text: guard.ScreenResult(True, [], 'lev unavailable', True),
                     record_incident=no_incident), 'send_system_message': lambda *args: None}
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    exec(compile(module, '<production-gate-dry-run>', 'exec'), namespace)
    save_case('production_gate_hold_no_incident', True,
              lambda: asyncio.run(namespace['gate_incoming_message']('synthetic-user', 'synthetic-text')))

report['matches'] = sum(row['matches'] for row in report['cases'])
Path('privacy-dry-run-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({'cases': len(report['cases']), 'matches': report['matches'], 'external_requests_sent': 0}))
