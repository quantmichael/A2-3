from database import get_connection

def show_review(review_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            raw_id,
            review_text,
            rating,
            review_date,
            product,
            sentiment,
            confidence,
            cleaned_at,
            analyzed_at
        FROM clean_reviews
        WHERE id = ?
        """,
        (review_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        print(f"ID {review_id} 리뷰를 찾을 수 없습니다.")
        return

    (
        review_id,
        raw_id,
        review_text,
        rating,
        review_date,
        product,
        sentiment,
        confidence,
        cleaned_at,
        analyzed_at,
    ) = row

    print("===== 리뷰 상세 =====")
    print(f"ID          : {review_id}")
    print(f"RAW ID      : {raw_id}")
    print(f"제품명       : {product}")
    print(f"별점         : {rating}")
    print(f"작성일       : {review_date}")
    print(f"감정         : {sentiment}")
    print(f"신뢰도       : {confidence}")
    print(f"정제일       : {cleaned_at}")
    print(f"분석일       : {analyzed_at}")
    print(f"리뷰         : {review_text}")
    

def list_reviews(sentiment=None, rating=None, date_from=None, date_to=None, page=1, page_size=10, sort="id_asc"):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            rating,
            sentiment,
            confidence,
            review_date,
            review_text
        FROM clean_reviews
    """

    conditions = []
    params = []

    if date_from:
        conditions.append("review_date >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("review_date <= ?")
        params.append(date_to)

    if sentiment:
        conditions.append("sentiment = ?")
        params.append(sentiment)

    if rating:
        conditions.append("rating = ?")
        params.append(rating)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    sort_map = {
        "id_asc": "id ASC",
        "id_desc": "id DESC",
        "rating_asc": "rating ASC",
        "rating_desc": "rating DESC",
        "confidence_asc": "confidence ASC",
        "confidence_desc": "confidence DESC",
        "date_asc": "review_date ASC",
        "date_desc": "review_date DESC",
    }

    order_by = sort_map.get(sort, "id ASC")

    query += f" ORDER BY {order_by}"

    offset = (page - 1) * page_size

    query += " LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    cursor.execute(query, params)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("조회할 리뷰가 없습니다.")
        return

    print(
        f"{'ID':<5}"
        f"{'별점':<6}"
        f"{'감정':<12}"
        f"{'신뢰도':<10}"
        f"{'날짜':<12}"
        f"리뷰"
    )

    print("-" * 80)

    for review_id, rating, sentiment, confidence, review_date, review_text in rows:

        confidence_text = (
            f"{confidence:.2f}"
            if confidence is not None
            else "-"
        )

        sentiment_text = (
            sentiment
            if sentiment is not None
            else "-"
        )

        print(
            f"{review_id:<5}"
            f"{rating:<6}"
            f"{sentiment_text:<12}"
            f"{confidence_text:<10}"
            f"{review_date:<12}"
            f"{review_text}"
        )