import pandas as pd

from database import get_connection


MIN_REVIEW_LENGTH = 6


def normalize_text(text):
    """앞뒤 공백과 연속된 공백을 정리합니다."""

    if text is None:
        return ""

    return " ".join(str(text).split())


def normalize_date(date_value):
    """날짜를 YYYY-MM-DD 형식으로 통일합니다."""

    if not date_value:
        return None

    parsed_date = pd.to_datetime(date_value, errors="coerce")

    if pd.isna(parsed_date):
        return None

    return parsed_date.strftime("%Y-%m-%d")


def clean_reviews():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, review_text, rating, review_date, product
        FROM raw_reviews
        ORDER BY id
    """)

    rows = cursor.fetchall()

    inserted = 0
    duplicate_count = 0
    invalid_rating_count = 0
    short_review_count = 0
    invalid_date_count = 0
    empty_review_count = 0
    already_cleaned_count = 0

    # 이미 clean_reviews에 들어간 raw_id 확인
    cursor.execute("SELECT raw_id FROM clean_reviews")
    processed_raw_ids = {row[0] for row in cursor.fetchall()}

    # 기존 정제 데이터의 중복 기준
    cursor.execute("""
        SELECT review_text, product
        FROM clean_reviews
    """)

    existing_reviews = {
        (row[0], row[1])
        for row in cursor.fetchall()
    }

    for raw_id, review_text, rating, review_date, product in rows:

        # 이미 처리된 원본
        if raw_id in processed_raw_ids:
            already_cleaned_count += 1
            continue

        # 1. 리뷰 텍스트 정규화
        cleaned_text = normalize_text(review_text)

        # 2. 빈 리뷰 확인
        if not cleaned_text:
            empty_review_count += 1
            continue

        # 3. 짧은 리뷰 확인
        if len(cleaned_text) < MIN_REVIEW_LENGTH:
            short_review_count += 1
            continue

        # 4. 별점 검증
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            invalid_rating_count += 1
            continue

        if rating < 1 or rating > 5:
            invalid_rating_count += 1
            continue

        # 5. 날짜 정규화
        cleaned_date = normalize_date(review_date)

        if cleaned_date is None:
            invalid_date_count += 1
            continue

        # 6. 중복 확인
        duplicate_key = (cleaned_text, product)

        if duplicate_key in existing_reviews:
            duplicate_count += 1
            continue

        # 7. clean_reviews 저장
        cursor.execute(
            """
            INSERT INTO clean_reviews
            (
                raw_id,
                review_text,
                rating,
                review_date,
                product
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                raw_id,
                cleaned_text,
                rating,
                cleaned_date,
                product,
            ),
        )

        existing_reviews.add(duplicate_key)
        inserted += 1

    conn.commit()
    conn.close()

    print("===== 데이터 정제 결과 =====")
    print(f"RAW 데이터       : {len(rows)}건")
    print(f"정제 완료        : {inserted}건")
    print(f"중복 제외        : {duplicate_count}건")
    print(f"짧은 리뷰 제외   : {short_review_count}건")
    print(f"별점 오류 제외    : {invalid_rating_count}건")
    print(f"날짜 오류 제외    : {invalid_date_count}건")
    print(f"빈 리뷰 제외      : {empty_review_count}건")
    print(f"기존 정제 데이터  : {already_cleaned_count}건")


if __name__ == "__main__":
    clean_reviews()