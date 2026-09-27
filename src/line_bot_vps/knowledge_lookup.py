"""Nearest learned knowledge for a statement, across all sisters (facts are facts).

Used before a paid Grok lookup: if the bot already verified something, it should not pay again.
Opens its own short-lived DB connection, because callers run in worker threads and the bot's
shared connection is not safe to use from several threads at once.
"""

import logging
import os
from typing import List

logger = logging.getLogger(__name__)

MIN_SIMILARITY = 0.5
LIMIT = 5


def lookup_known_facts(statement: str, limit: int = LIMIT, min_similarity: float = MIN_SIMILARITY) -> List[dict]:
    """[{word, meaning, similarity}], best first. Any failure means "nothing known"."""
    try:
        import openai
        from .postgresql_manager import PostgreSQLManager

        openai.api_key = os.getenv("OPENAI_API_KEY")
        embedding = openai.embeddings.create(model="text-embedding-3-small", input=statement).data[0].embedding
        vector = "[" + ",".join(map(str, embedding)) + "]"
        pg = PostgreSQLManager()
        if not pg.connect():
            return []
        try:
            with pg.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT word, meaning, 1 - (embedding <=> %s::vector) AS similarity "
                    "FROM learned_knowledge WHERE embedding IS NOT NULL "
                    "ORDER BY embedding <=> %s::vector LIMIT %s", (vector, vector, limit))
                rows = cursor.fetchall()
        finally:
            pg.disconnect()
        return [{"word": r[0], "meaning": r[1], "similarity": float(r[2])} for r in rows if float(r[2]) >= min_similarity]
    except Exception as exc:
        logger.warning("knowledge lookup failed: %s", type(exc).__name__)
        return []
