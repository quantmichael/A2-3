import sqlite3
from pathlib import Path


DB_PATH = Path("data/reviews.db")


def get_connection():
    """SQLite 데이터베이스 연결 객체를 반환합니다."""
    return sqlite3.connect(DB_PATH)


def create_tables():
    """프로젝트에서 사용할 기본 테이블을 생성합니다."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_text TEXT NOT NULL,
            rating INTEGER,
            review_date TEXT,
            product TEXT,
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clean_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            rating INTEGER,
            review_date TEXT,
            product TEXT,
            sentiment TEXT,
            confidence REAL,
            cleaned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            analyzed_at TEXT,
            FOREIGN KEY (raw_id) REFERENCES raw_reviews(id)
        )
    """)    

    conn.commit()
    conn.close()

    print("데이터베이스 테이블 생성 완료")


if __name__ == "__main__":
    create_tables()