#!/usr/bin/env python3
"""
Comprehensive audit of Botan's 98 memories
Check for quality issues, inconsistencies, and errors
"""

import sqlite3
import re
from typing import List, Dict, Tuple


class BotanMemoryAuditor:
    def __init__(self, db_path="sisters_memory.db"):
        self.db_path = db_path
        self.issues = []
        
    def load_all_memories(self):
        """Load all 98 memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT bm.memory_id, bm.event_id, sse.botan_absolute_day, 
                   sse.event_name, bm.botan_emotion, bm.botan_action,
                   bm.botan_thought, bm.diary_entry
            FROM botan_memories bm
            JOIN sister_shared_events sse ON bm.event_id = sse.event_id
            ORDER BY sse.botan_absolute_day
        """)
        
        memories = []
        for row in cursor.fetchall():
            memory_id, event_id, abs_day, event_name, emotion, action, thought, diary = row
            age_years = abs_day // 365
            age_months = (abs_day % 365) // 30
            
            memories.append({
                'memory_id': memory_id,
                'event_id': event_id,
                'age_years': age_years,
                'age_months': age_months,
                'event_name': event_name,
                'emotion': emotion,
                'action': action,
                'thought': thought or '',
                'diary': diary or ''
            })
        
        conn.close()
        return memories
    
    def check_pronouns(self, memories):
        """Check for incorrect pronouns"""
        print("\n【検閲1】一人称の確認")
        print("="*60)
        
        issues = []
        male_pronouns = ['俺', '僕', 'ボク', 'おれ', 'ぼく']
        
        for mem in memories:
            problems = []
            
            for pronoun in male_pronouns:
                if pronoun in mem['thought']:
                    problems.append(f"思考に「{pronoun}」")
                if pronoun in mem['diary']:
                    problems.append(f"日記に「{pronoun}」")
            
            if problems:
                issues.append({
                    'event_id': mem['event_id'],
                    'age': f"{mem['age_years']}歳{mem['age_months']}ヶ月",
                    'problems': problems,
                    'thought': mem['thought'][:100],
                    'diary': mem['diary'][:100]
                })
        
        if issues:
            print(f"⚠️  {len(issues)}件の問題を発見\n")
            for issue in issues:
                print(f"Event #{issue['event_id']} ({issue['age']})")
                for problem in issue['problems']:
                    print(f"  - {problem}")
                print()
        else:
            print("✅ 問題なし\n")
        
        return issues
    
    def check_gender_references(self, memories):
        """Check for incorrect gender references"""
        print("\n【検閲2】性別に関する表現の確認")
        print("="*60)
        
        issues = []
        male_refs = ['男', '息子', '彼', '王子']
        
        for mem in memories:
            problems = []
            text = mem['thought'] + ' ' + mem['diary']
            
            # Check for male references (excluding specific OK contexts)
            for ref in male_refs:
                if ref in text:
                    # Check if it's NOT referring to someone else
                    context = text[max(0, text.find(ref)-20):min(len(text), text.find(ref)+20)]
                    if '翔太' not in context and '太郎' not in context and 'お父さん' not in context:
                        problems.append(f"「{ref}」という表現（文脈確認必要）")
            
            if problems:
                issues.append({
                    'event_id': mem['event_id'],
                    'age': f"{mem['age_years']}歳{mem['age_months']}ヶ月",
                    'problems': problems,
                    'context': text[:150]
                })
        
        if issues:
            print(f"⚠️  {len(issues)}件の問題を発見（要確認）\n")
            for issue in issues:
                print(f"Event #{issue['event_id']} ({issue['age']})")
                for problem in issue['problems']:
                    print(f"  - {problem}")
                print(f"  文脈: {issue['context']}...\n")
        else:
            print("✅ 問題なし\n")
        
        return issues
    
    def check_age_appropriateness(self, memories):
        """Check for age-inappropriate expressions"""
        print("\n【検閲3】年齢相応の表現チェック")
        print("="*60)
        
        issues = []
        
        for mem in memories:
            problems = []
            age = mem['age_years']
            
            # ギャル語は12歳以降に登場すべき
            gyaru_words = ['マジで', 'ヤバ', '～じゃん', 'めっちゃ', 'ウケる']
            if age < 11:
                for word in gyaru_words:
                    if word in mem['thought'] or word in mem['diary']:
                        # 7-10歳で「めっちゃ」「マジ」は許容範囲
                        if age >= 7 and word in ['めっちゃ', 'マジで']:
                            continue
                        problems.append(f"{age}歳でギャル語「{word}」（早すぎる可能性）")
            
            # 0-2歳は思考・日記がほぼないはず
            if age <= 2:
                if len(mem['thought']) > 10 or len(mem['diary']) > 10:
                    problems.append(f"{age}歳で詳細な思考/日記（不自然）")
            
            if problems:
                issues.append({
                    'event_id': mem['event_id'],
                    'age': f"{mem['age_years']}歳{mem['age_months']}ヶ月",
                    'problems': problems
                })
        
        if issues:
            print(f"⚠️  {len(issues)}件の問題を発見\n")
            for issue in issues:
                print(f"Event #{issue['event_id']} ({issue['age']})")
                for problem in issue['problems']:
                    print(f"  - {problem}")
                print()
        else:
            print("✅ 問題なし\n")
        
        return issues
    
    def check_language_consistency(self, memories):
        """Check language usage consistency"""
        print("\n【検閲4】言語使用の一貫性チェック")
        print("="*60)
        
        issues = []
        
        for mem in memories:
            problems = []
            age = mem['age_years']
            
            # LA期(3-10歳)は多言語OK、それ以外で英語・中国語は要確認
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', mem['thought'] + mem['diary']))
            has_english_sentence = bool(re.search(r'\b[A-Z][a-z]+\s+[a-z]+\b', mem['thought'] + mem['diary']))
            
            if age > 10:  # 日本帰国後
                if has_chinese:
                    # 中国語の使用頻度チェック（たまに使うのはOK）
                    chinese_count = len(re.findall(r'[\u4e00-\u9fff]', mem['thought'] + mem['diary']))
                    if chinese_count > 20:
                        problems.append(f"{age}歳で中国語多用（帰国後は減るはず）")
            
            if problems:
                issues.append({
                    'event_id': mem['event_id'],
                    'age': f"{mem['age_years']}歳{mem['age_months']}ヶ月",
                    'problems': problems
                })
        
        if issues:
            print(f"⚠️  {len(issues)}件の問題を発見\n")
            for issue in issues:
                print(f"Event #{issue['event_id']} ({issue['age']})")
                for problem in issue['problems']:
                    print(f"  - {problem}")
                print()
        else:
            print("✅ 問題なし\n")
        
        return issues
    
    def check_empty_fields(self, memories):
        """Check for unexpectedly empty fields"""
        print("\n【検閲5】空欄フィールドのチェック")
        print("="*60)
        
        issues = []
        
        for mem in memories:
            problems = []
            age = mem['age_years']
            
            # 3歳以上で思考が空欄は不自然
            if age >= 3 and not mem['thought']:
                problems.append("思考が空欄")
            
            # 3歳以上で日記が空欄は不自然
            if age >= 3 and not mem['diary']:
                problems.append("日記が空欄")
            
            # 感情・行動が空欄
            if not mem['emotion']:
                problems.append("感情が空欄")
            if not mem['action']:
                problems.append("行動が空欄")
            
            if problems:
                issues.append({
                    'event_id': mem['event_id'],
                    'age': f"{mem['age_years']}歳{mem['age_months']}ヶ月",
                    'problems': problems
                })
        
        if issues:
            print(f"⚠️  {len(issues)}件の問題を発見\n")
            for issue in issues[:10]:  # 最初の10件のみ表示
                print(f"Event #{issue['event_id']} ({issue['age']})")
                for problem in issue['problems']:
                    print(f"  - {problem}")
                print()
            if len(issues) > 10:
                print(f"... 他 {len(issues)-10}件\n")
        else:
            print("✅ 問題なし\n")
        
        return issues
    
    def check_character_consistency(self, memories):
        """Check character setting consistency"""
        print("\n【検閲6】キャラクター設定の一貫性チェック")
        print("="*60)
        
        issues = []
        
        # Key character traits
        gyaru_indicators = ['ギャル', 'ファッション', 'メイク', 'ネイル']
        dance_indicators = ['ダンス', '踊']
        vtuber_indicators = ['VTuber', 'Vチューバー', '配信']
        
        # Count occurrences
        gyaru_count = sum(1 for m in memories if any(ind in m['thought']+m['diary'] for ind in gyaru_indicators))
        dance_count = sum(1 for m in memories if any(ind in m['thought']+m['diary'] for ind in dance_indicators))
        vtuber_count = sum(1 for m in memories if any(ind in m['thought']+m['diary'] for ind in vtuber_indicators))
        
        print(f"ギャル関連の記憶: {gyaru_count}件")
        print(f"ダンス関連の記憶: {dance_count}件")
        print(f"VTuber関連の記憶: {vtuber_count}件")
        
        if vtuber_count == 0:
            print("\n⚠️  VTuber関連の記憶がありません（牡丹の重要な特徴）")
            issues.append("VTuber関連記憶なし")
        
        print()
        return issues
    
    def run_full_audit(self):
        """Run comprehensive audit"""
        print("\n" + "="*60)
        print("牡丹の記憶データベース 包括的検閲")
        print("="*60)
        
        memories = self.load_all_memories()
        print(f"\n総記憶数: {len(memories)}件")
        
        all_issues = {}
        
        all_issues['pronouns'] = self.check_pronouns(memories)
        all_issues['gender'] = self.check_gender_references(memories)
        all_issues['age'] = self.check_age_appropriateness(memories)
        all_issues['language'] = self.check_language_consistency(memories)
        all_issues['empty'] = self.check_empty_fields(memories)
        all_issues['character'] = self.check_character_consistency(memories)
        
        # Summary
        print("\n" + "="*60)
        print("検閲結果サマリー")
        print("="*60)
        
        total_issues = sum(len(v) if isinstance(v, list) else 1 for v in all_issues.values() if v)
        
        print(f"一人称の問題: {len(all_issues['pronouns'])}件")
        print(f"性別表現の問題: {len(all_issues['gender'])}件")
        print(f"年齢不適切: {len(all_issues['age'])}件")
        print(f"言語の一貫性: {len(all_issues['language'])}件")
        print(f"空欄フィールド: {len(all_issues['empty'])}件")
        print(f"キャラクター設定: {len(all_issues['character']) if isinstance(all_issues['character'], list) else 0}件")
        
        print(f"\n合計問題数: {total_issues}件")
        
        if total_issues == 0:
            print("\n✅ すべての検閲項目をクリアしました！")
        else:
            print("\n⚠️  修正が必要な項目があります")
        
        print("="*60)
        
        return all_issues


if __name__ == "__main__":
    auditor = BotanMemoryAuditor()
    auditor.run_full_audit()
