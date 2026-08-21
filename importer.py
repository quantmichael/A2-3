import pandas as pd

from database import get_connection


def import_csv(file_path):
    """CSV 리뷰 데이터를 raw_reviews 테이블에 저장합니다."""

    df = pd.read_csv(file_path)

    print(f"CSV 데이터: {len(df)}건")

    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():

        review_text = row["review_text"]
        rating = row["rating"]
        review_date = row["review_date"]
        product = row["product"]

        cursor.execute(
            """
            SELECT id
            FROM raw_reviews
            WHERE review_text = ?
              AND product = ?
            LIMIT 1
            """,
            (
                review_text,
                product,
            ),
        )

        existing = cursor.fetchone()

        if existing:
            skipped += 1
            continue

        cursor.execute(
            """
            INSERT INTO raw_reviews
            (
                review_text,
                rating,
                review_date,
                product
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                review_text,
                rating,
                review_date,
                product,
            ),
        )

        inserted += 1

    conn.commit()
    conn.close()

    print("===== Import 결과 =====")
    print(f"입력 데이터 : {len(df)}건")
    print(f"추가       : {inserted}건")
    print(f"중복 제외   : {skipped}건")


if __name__ == "__main__":
    import_csv("data/reviews.csv")