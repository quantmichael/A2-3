from database import get_connection


def show_stats():
    conn = get_connection()
    cursor = conn.cursor()

    # 전체 리뷰 수
    cursor.execute("""
        SELECT COUNT(*)
        FROM clean_reviews
    """)
    total_count = cursor.fetchone()[0]

    # 평균 confidence
    cursor.execute("""
        SELECT AVG(confidence)
        FROM clean_reviews
        WHERE confidence IS NOT NULL
    """)
    avg_confidence = cursor.fetchone()[0]

    # 감정별 건수
    cursor.execute("""
        SELECT sentiment, COUNT(*)
        FROM clean_reviews
        GROUP BY sentiment
        ORDER BY sentiment
    """)
    sentiment_rows = cursor.fetchall()

    # 별점 분포
    cursor.execute("""
        SELECT rating, COUNT(*)
        FROM clean_reviews
        GROUP BY rating
        ORDER BY rating
    """)
    rating_rows = cursor.fetchall()

    # 별점별 감정 분포
    cursor.execute("""
        SELECT
            rating,
            sentiment,
            COUNT(*)
        FROM clean_reviews
        WHERE sentiment IS NOT NULL
        GROUP BY rating, sentiment
        ORDER BY rating, sentiment
    """)
    rating_sentiment_rows = cursor.fetchall()

    # 일별 감정 변화
    cursor.execute("""
        SELECT
            review_date,
            sentiment,
            COUNT(*)
        FROM clean_reviews
        WHERE sentiment IS NOT NULL
        GROUP BY review_date, sentiment
        ORDER BY review_date
    """)
    daily_sentiment_rows = cursor.fetchall()

    # 주별 감정 변화
    cursor.execute("""
        SELECT
            strftime('%Y-%W', review_date) AS week,
            sentiment,
            COUNT(*)
        FROM clean_reviews
        WHERE sentiment IS NOT NULL
        GROUP BY week, sentiment
        ORDER BY week
    """)

    weekly_sentiment_rows = cursor.fetchall()

    # 월별 감정 변화
    cursor.execute("""
        SELECT
            strftime('%Y-%m', review_date) AS month,
            sentiment,
            COUNT(*)
        FROM clean_reviews
        WHERE sentiment IS NOT NULL
        GROUP BY month, sentiment
        ORDER BY month
    """)

    monthly_sentiment_rows = cursor.fetchall()

    conn.close()

    # ------------------------------------------
    # 출력
    # ------------------------------------------

    print("===== 리뷰 통계 =====")
    print(f"전체 리뷰 수 : {total_count}건")

    if avg_confidence is not None:
        print(f"평균 신뢰도  : {avg_confidence:.2f}")
    else:
        print("평균 신뢰도  : -")

    # 감정 분포
    print("\n[감정 분포]")

    for sentiment, count in sentiment_rows:
        ratio = (
            count / total_count * 100
            if total_count > 0
            else 0
        )

        print(
            f"{sentiment:<8}: "
            f"{count}건 "
            f"({ratio:.1f}%)"
        )

    # 별점 분포
    print("\n[별점 분포]")

    for rating, count in rating_rows:
        print(f"{rating}점 : {count}건")

    # 별점별 감정 분포
    print("\n[별점별 감정 분포]")

    for rating in range(1, 6):

        counts = {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
        }

        for row_rating, sentiment, count in rating_sentiment_rows:
            if row_rating == rating:
                counts[sentiment] = count

        print(
            f"{rating}점 : "
            f"positive {counts['positive']}건 | "
            f"neutral {counts['neutral']}건 | "
            f"negative {counts['negative']}건"
        )

    # 일별 감정 변화
    print("\n[일별 감정 변화]")

    daily_data = {}

    for review_date, sentiment, count in daily_sentiment_rows:

        if review_date not in daily_data:
            daily_data[review_date] = {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
            }

        daily_data[review_date][sentiment] = count

    for review_date, counts in daily_data.items():
        print(
            f"{review_date} : "
            f"positive {counts['positive']}건 | "
            f"neutral {counts['neutral']}건 | "
            f"negative {counts['negative']}건"
        )

    # 주별 감정 변화
    print("\n[주별 감정 변화]")

    weekly_data = {}

    for week, sentiment, count in weekly_sentiment_rows:
        if week not in weekly_data:
            weekly_data[week] = {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
            }

        weekly_data[week][sentiment] = count

    for week, counts in weekly_data.items():
        print(
            f"{week}주 : "
            f"positive {counts['positive']}건 | "
            f"neutral {counts['neutral']}건 | "
            f"negative {counts['negative']}건"
        )

    # 월별 감정 변화
    print("\n[월별 감정 변화]")

    monthly_data = {}

    for month, sentiment, count in monthly_sentiment_rows:
        if month not in monthly_data:
            monthly_data[month] = {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
            }

        monthly_data[month][sentiment] = count

    for month, counts in monthly_data.items():
        print(
            f"{month} : "
            f"positive {counts['positive']}건 | "
            f"neutral {counts['neutral']}건 | "
            f"negative {counts['negative']}건"
        )