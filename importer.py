import pandas as pd

from database import get_connection


def import_csv(file_path):
    """CSV 리뷰 데이터를 raw_reviews 테이블에 저장합니다."""

    df = pd.read_csv(file_path)

    print(f"CSV 데이터: {len(df)}건")

    conn = get_connection()
    cursor = conn.cursor()

    for _, row in df.iterrows():

        cursor.execute(
            """
            INSERT INTO raw_reviews
            (review_text, rating, review_date, product)
            VALUES (?, ?, ?, ?)
            """,
            (
                row["review_text"],
                row["rating"],
                row["review_date"],
                row["product"],
            ),
        )

    conn.commit()
    conn.close()

    print(f"Import 완료: {len(df)}건")


if __name__ == "__main__":
    import_csv("data/reviews.csv")