"""
Knowledge Manager
=================

Manages static knowledge about VTubers, units, etc.
This provides Tier 1 (most reliable) information.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DB_PATH


class KnowledgeManager:
    """Manages VTuber knowledge base"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(self.db_path))

    def get_unit_info(self, unit_name: str) -> Optional[Dict]:
        """
        Get unit information and members

        Args:
            unit_name: Unit name (e.g., 'ド珍組')

        Returns:
            dict: {
                'unit_name': str,
                'description': str,
                'official': bool,
                'members': list of VTuber names
            }
        """
        cursor = self.conn.cursor()

        # Get unit info
        cursor.execute("""
        SELECT unit_name, description, official
        FROM vtuber_units
        WHERE unit_name = ?
        """, (unit_name,))

        result = cursor.fetchone()
        if not result:
            return None

        unit_info = {
            'unit_name': result[0],
            'description': result[1],
            'official': bool(result[2])
        }

        # Get members
        cursor.execute("""
        SELECT v.name
        FROM vtuber_unit_members um
        JOIN vtubers v ON um.vtuber_id = v.vtuber_id
        JOIN vtuber_units u ON um.unit_id = u.unit_id
        WHERE u.unit_name = ?
        ORDER BY v.name
        """, (unit_name,))

        unit_info['members'] = [row[0] for row in cursor.fetchall()]

        return unit_info

    def get_vtuber_nicknames(self, vtuber_name: str) -> List[str]:
        """
        Get all nicknames for a VTuber

        Args:
            vtuber_name: VTuber's official name

        Returns:
            list: List of nicknames
        """
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT n.nickname, n.nickname_type
        FROM vtuber_nicknames n
        JOIN vtubers v ON n.vtuber_id = v.vtuber_id
        WHERE v.name = ?
        ORDER BY n.is_primary DESC, n.nickname
        """, (vtuber_name,))

        return [(row[0], row[1]) for row in cursor.fetchall()]

    def get_vtuber_trivia(self, vtuber_name: str) -> List[Dict]:
        """
        Get trivia about a VTuber

        Args:
            vtuber_name: VTuber's official name

        Returns:
            list: List of trivia items
        """
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT category, content, verified
        FROM vtuber_trivia t
        JOIN vtubers v ON t.vtuber_id = v.vtuber_id
        WHERE v.name = ? AND verified = 1
        ORDER BY category
        """, (vtuber_name,))

        trivia = []
        for category, content, verified in cursor.fetchall():
            trivia.append({
                'category': category,
                'content': content
            })

        return trivia

    def search_unit_by_keyword(self, keyword: str) -> List[str]:
        """
        Search for units containing keyword

        Args:
            keyword: Search keyword

        Returns:
            list: List of unit names
        """
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT unit_name
        FROM vtuber_units
        WHERE unit_name LIKE ? OR description LIKE ?
        """, (f'%{keyword}%', f'%{keyword}%'))

        return [row[0] for row in cursor.fetchall()]

    def get_all_units(self) -> List[str]:
        """Get all unit names"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT unit_name FROM vtuber_units ORDER BY unit_name")

        return [row[0] for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
