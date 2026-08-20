import json
import os
import time
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError
from pydantic import BaseModel, Field

from database import get_connection

import logging
from pathlib import Path

# ==========================================
# 기본 설정
# ==========================================
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "analyzer.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY를 찾을 수 없습니다.")

client = genai.Client(api_key=api_key)

BATCH_SIZE = 10
MAX_RETRIES = 3


# ==========================================
# Gemini 응답 구조
# ==========================================

class SentimentResult(BaseModel):
    id: int
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)


class BatchSentimentResult(BaseModel):
    results: list[SentimentResult]


# ==========================================
# DB에서 미분석 리뷰 조회
# ==========================================

def get_unanalyzed_reviews(limit=BATCH_SIZE):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, review_text
        FROM clean_reviews
        WHERE sentiment IS NULL
        ORDER BY id
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==========================================
# Gemini 배치 감정분석
# ==========================================

def analyze_batch(reviews):
    review_data = [
        {
            "id": review_id,
            "review_text": review_text,
        }
        for review_id, review_text in reviews
    ]

    prompt = f"""
다음 고객 리뷰들의 감정을 각각 분석하세요.

감정은 반드시 아래 세 가지 중 하나만 선택하세요.
- positive
- negative
- neutral

각 리뷰에 대해 다음 값을 반환하세요.
- id
- sentiment
- confidence

confidence는 0.0에서 1.0 사이 숫자입니다.

입력된 모든 리뷰를 빠짐없이 분석하세요.
입력된 리뷰의 id를 그대로 유지하세요.

리뷰 목록:
{json.dumps(review_data, ensure_ascii=False)}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BatchSentimentResult,
        ),
    )

    return BatchSentimentResult.model_validate_json(
        response.text
    )


# ==========================================
# API 오류 재시도
# ==========================================

def analyze_batch_with_retry(reviews):
    for attempt in range(1, MAX_RETRIES + 1):

        try:
            return analyze_batch(reviews)

        except ServerError as e:

            if e.code == 503:
                wait_time = attempt * 3

                logger.warning(
                    f"Gemini 503 발생 - 재시도 {attempt}/{MAX_RETRIES}"
                )

                print(
                    f"Gemini 서버 과부하 (503) - "
                    f"{wait_time}초 후 재시도 "
                    f"({attempt}/{MAX_RETRIES})"
                )

                time.sleep(wait_time)

            else:
                logger.error(f"Gemini API 오류: {e}")
                raise

    print("Gemini API 재시도 실패")

    
    return None

def validate_batch_results(reviews, results):
    """입력 리뷰와 Gemini 응답의 ID가 정확히 일치하는지 검사합니다."""

    input_ids = {review_id for review_id, _ in reviews}
    result_ids = [result.id for result in results]

    result_id_set = set(result_ids)

    missing_ids = input_ids - result_id_set

    duplicate_ids = {
        result_id
        for result_id in result_ids
        if result_ids.count(result_id) > 1
    }

    unexpected_ids = result_id_set - input_ids

    if missing_ids:
        logger.error(
            f"Gemini 응답 누락 ID: {sorted(missing_ids)}"
        )

    if duplicate_ids:
        logger.error(
            f"Gemini 응답 중복 ID: {sorted(duplicate_ids)}"
        )

    if unexpected_ids:
        logger.error(
            f"입력에 없는 Gemini 응답 ID: {sorted(unexpected_ids)}"
        )

    if missing_ids or duplicate_ids or unexpected_ids:
        return False

    return True

# ==========================================
# 분석 결과 DB 저장
# ==========================================

def update_batch_sentiments(results):
    conn = get_connection()
    cursor = conn.cursor()

    for result in results:

        cursor.execute(
            """
            UPDATE clean_reviews
            SET sentiment = ?,
                confidence = ?,
                analyzed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                result.sentiment,
                result.confidence,
                result.id,
            ),
        )

    conn.commit()
    conn.close()


# ==========================================
# 전체 미분석 리뷰 자동 처리
# ==========================================

def analyze_all_unanalyzed():
    total_processed = 0
    batch_number = 1

    while True:

        reviews = get_unanalyzed_reviews()

        if not reviews:
            break

        print(
            f"\n===== Batch {batch_number} "
            f"({len(reviews)}건) ====="
        )

        for review_id, review_text in reviews:
            print(f"[{review_id}] {review_text}")

        batch_result = analyze_batch_with_retry(reviews)

        if batch_result is None:
            print("API 오류로 분석을 중단합니다.")
            break

        print("\nGemini 분석 결과")

        for result in batch_result.results:
            print(
                f"ID: {result.id} | "
                f"감정: {result.sentiment} | "
                f"신뢰도: {result.confidence}"
            )

        is_valid = validate_batch_results(
            reviews,
            batch_result.results,
        )

        if not is_valid:
            print("Gemini 응답 검증 실패 - 현재 배치를 저장하지 않습니다.")
            logger.error("배치 결과 검증 실패")
            break

        update_batch_sentiments(
            batch_result.results
        )

        processed_count = len(
            batch_result.results
        )

        total_processed += processed_count

        print(
            f"DB 저장 완료: "
            f"{processed_count}건"
        )

        batch_number += 1

    print("\n==========================")
    print(
        f"전체 분석 완료: "
        f"{total_processed}건"
    )
    print("==========================")


# ==========================================
# 프로그램 시작
# ==========================================

if __name__ == "__main__":
    analyze_all_unanalyzed()