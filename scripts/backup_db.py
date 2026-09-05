"""
Back up the SQLite database to data/backups/, timestamped.

Run manually:
    python scripts/backup_db.py

Or schedule it (e.g. Windows Task Scheduler, daily) to run automatically.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/manje_lakay.db")
BACKUP_DIR = Path("data/backups")
KEEP_LAST_N = 14  # prune older backups so this folder doesn't grow forever


def backup_database() -> Path | None:
    if not DB_PATH.exists():
        print(f"No database found at {DB_PATH}, nothing to back up.")
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"manje_lakay_{timestamp}.db"

    # SQLite's own backup API, not a raw file copy -- this is safe to run
    # even while the app is actively running and writing to the database.
    # A plain file copy could grab a half-written page mid-transaction and
    # produce a corrupt backup; this API handles that correctly.
    source = sqlite3.connect(DB_PATH)
    dest = sqlite3.connect(backup_path)
    with dest:
        source.backup(dest)
    source.close()
    dest.close()

    print(f"Backed up to {backup_path}")
    _prune_old_backups()
    return backup_path


def _prune_old_backups() -> None:
    """Keep only the most recent KEEP_LAST_N backup files."""
    backups = sorted(BACKUP_DIR.glob("manje_lakay_*.db"))
    excess = len(backups) - KEEP_LAST_N
    for old_backup in backups[:max(excess, 0)]:
        old_backup.unlink()
        print(f"Removed old backup: {old_backup.name}")


if __name__ == "__main__":
    backup_database()