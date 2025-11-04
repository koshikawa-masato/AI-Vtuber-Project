#!/usr/bin/env python3
"""
Improved comprehensive audit of Botan's memories
Fixed false positives in gender references and language detection
"""

import sqlite3
import re
from typing import List, Dict


class BotanMemoryAuditor:
    def __init__(self, db_path="sisters_memory.db"):
        self.db_path = db_path
        
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
        male_pronouns = ['俺', '僕', 'ぼく', 'おれ']
        
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
                    'problems': problems
                })
        
        if issues:
            print(f"❌ {len(issues)}件の問題を発見\n")
            for issue in issues:
                print(f"Event #{issue['event_id']} ({issue['age']})")
                for problem in issue['problems']:
                    print(f"  - {problem}")
                print()
        else:
            print("✅ 問題なし\n")
        
        return issues
    
    def check_age_appropriateness(self, memories):
        """Check for age-inappropriate expressions"""
        print("\n【検閲2】年齢相応の表現チェック")
        print("="*60)
        
        issues = []
        
        for mem in memories:
            problems = []
            age = mem['age_years']
            
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
            print(f"❌ {len(issues)}件の問題を発見\n")
            for issue in issues:
                print(f"Event #{issue['event_id']} ({issue['age']})")
                for problem in issue['problems']:
                    print(f"  - {problem}")
                print()
        else:
            print("✅ 問題なし\n")
        
        return issues
    
    def check_chinese_actual_usage(self, memories):
        """Check for actual Chinese language usage (not just kanji)"""
        print("\n【検閲3】中国語固有表現のチェック")
        print("="*60)
        
        issues = []
        
        # Common Chinese expressions that should decrease after returning to Japan
        chinese_expressions = [
            '妈妈', '爸爸', '姐姐', '妹妹',  # Family terms
            '我们', '他们', '她们',  # Pronouns
            '你好', '谢谢', '对不起',  # Greetings
            '喜欢', '开心', '难过',  # Emotions (but these are also in Japanese kanji)
        ]
        
        for mem in memories:
            age = mem['age_years']
            
            # After age 10 (returned to Japan), Chinese expressions should be rare
            if age > 10:
                problems = []
                text = mem['thought'] + ' ' + mem['diary']
                
                for expr in chinese_expressions:
                    if expr in text:
                        problems.append(f"中国語表現「{expr}」")
                
                if problems:
                    issues.append({
                        'event_id': mem['event_id'],
                        'age': f"{mem['age_years']}歳{mem['age_months']}ヶ月",
                        'problems': problems
                    })
        
        if issues:
            print(f"⚠️  {len(issues)}件の中国語表現を発見\n")
            for issue in issues[:5]:  # Show first 5
                print(f"Event #{issue['event_id']} ({issue['age']})")
                for problem in issue['problems']:
                    print(f"  - {problem}")
                print()
            if len(issues) > 5:
                print(f"... 他 {len(issues)-5}件\n")
        else:
            print("✅ 問題なし\n")
        
        return issues
    
    def check_empty_fields(self, memories):
        """Check for unexpectedly empty fields"""
        print("\n【検閲4】空欄フィールドのチェック")
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
            print(f"❌ {len(issues)}件の問題を発見\n")
            for issue in issues[:5]:
                print(f"Event #{issue['event_id']} ({issue['age']})")
                for problem in issue['problems']:
                    print(f"  - {problem}")
                print()
            if len(issues) > 5:
                print(f"... 他 {len(issues)-5}件\n")
        else:
            print("✅ 問題なし\n")
        
        return issues
    
    def check_character_consistency(self, memories):
        """Check character setting consistency"""
        print("\n【検閲5】キャラクター設定の一貫性チェック")
        print("="*60)
        
        issues = []
        
        # Key character traits
        gyaru_indicators = ['ギャル', 'ファッション', 'メイク', 'ネイル', 'マジで', 'ヤバ', '～じゃん']
        dance_indicators = ['ダンス', '踊']
        vtuber_indicators = ['VTuber', 'Vチューバー', '配信', 'ストリーム', 'リスナー']
        
        # Count occurrences
        gyaru_count = sum(1 for m in memories if any(ind in m['thought']+m['diary'] for ind in gyaru_indicators))
        dance_count = sum(1 for m in memories if any(ind in m['thought']+m['diary'] for ind in dance_indicators))
        vtuber_count = sum(1 for m in memories if any(ind in m['thought']+m['diary'] for ind in vtuber_indicators))
        
        print(f"ギャル関連の記憶: {gyaru_count}件")
        print(f"ダンス関連の記憶: {dance_count}件")
        print(f"VTuber関連の記憶: {vtuber_count}件")
        
        recommendations = []
        if gyaru_count < 30:
            recommendations.append("ギャル語の使用頻度が低め（30件未満）")
        if dance_count < 5:
            recommendations.append("ダンス関連の記憶が少ない（5件未満）")
        if vtuber_count < 3:
            recommendations.append("VTuber関連の記憶が少ない（3件未満）")
        
        if recommendations:
            print("\n💡 推奨事項:")
            for rec in recommendations:
                print(f"  - {rec}")
        
        print()
        return recommendations
    
    def run_full_audit(self):
        """Run comprehensive audit"""
        print("\n" + "="*60)
        print("牡丹の記憶データベース 包括的検閲 v2")
        print("="*60)
        
        memories = self.load_all_memories()
        print(f"\n総記憶数: {len(memories)}件")
        
        all_issues = {}
        
        all_issues['pronouns'] = self.check_pronouns(memories)
        all_issues['age'] = self.check_age_appropriateness(memories)
        all_issues['chinese'] = self.check_chinese_actual_usage(memories)
        all_issues['empty'] = self.check_empty_fields(memories)
        all_issues['character'] = self.check_character_consistency(memories)
        
        # Summary
        print("\n" + "="*60)
        print("検閲結果サマリー（改良版）")
        print("="*60)
        
        total_critical = len(all_issues['pronouns']) + len(all_issues['age']) + len(all_issues['empty'])
        total_warnings = len(all_issues['chinese'])
        
        print(f"🔴 重大な問題:")
        print(f"  一人称の問題: {len(all_issues['pronouns'])}件")
        print(f"  年齢不適切: {len(all_issues['age'])}件")
        print(f"  空欄フィールド: {len(all_issues['empty'])}件")
        print(f"  小計: {total_critical}件")
        
        print(f"\n🟡 警告（要確認）:")
        print(f"  中国語固有表現: {len(all_issues['chinese'])}件")
        
        print(f"\n💡 推奨事項: {len(all_issues['character'])}件")
        
        if total_critical == 0:
            print("\n✅ すべての重大な問題は解決済みです！")
        else:
            print(f"\n⚠️  {total_critical}件の重大な問題が残っています")
        
        print("="*60)
        
        return all_issues


if __name__ == "__main__":
    auditor = BotanMemoryAuditor()
    auditor.run_full_audit()
