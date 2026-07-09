import logging
import os
import sys

import aiosqlite
from datetime import datetime

from backend.config import DATABASE_URL

logger = logging.getLogger(__name__)


def _ensure_db_parent_dir():
    db_dir = os.path.dirname(DATABASE_URL)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


async def init_db():
    _ensure_db_parent_dir()
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                label TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                grad_cam_path TEXT
            )
        ''')
        await db.commit()
    logger.info("Database initialized at %s", DATABASE_URL)


async def save_prediction(filename: str, label: str, confidence: float, grad_cam_path: str = None):
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute('''
                INSERT INTO predictions (filename, label, confidence, timestamp, grad_cam_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, label, confidence, datetime.now(), grad_cam_path))
            await db.commit()
    except Exception:
        logger.exception("Failed to save prediction for %s", filename)
        raise


async def get_all_predictions():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM predictions ORDER BY timestamp DESC') as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
