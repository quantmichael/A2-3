import argparse

from statistics import show_stats
from database import create_tables
from importer import import_csv
from cleaner import clean_reviews
from analyzer import analyze_all_unanalyzed
from viewer import list_reviews, show_review

def main():
    parser = argparse.ArgumentParser(
        description="고객 리뷰 AI 감정분석 시스템"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # -------------------------
    # import
    # -------------------------
    import_parser = subparsers.add_parser(
        "import",
        help="CSV 리뷰 데이터를 가져옵니다.",
    )

    import_parser.add_argument(
        "--file",
        required=True,
        help="가져올 CSV 파일 경로",
    )

    # -------------------------
    # clean
    # -------------------------
    subparsers.add_parser(
        "clean",
        help="원본 리뷰 데이터를 정제합니다.",
    )

    # -------------------------
    # list
    # -------------------------
    list_parser = subparsers.add_parser(
        "list",
        help="정제된 리뷰 목록을 조회합니다.",
    )

    list_parser.add_argument(
        "--sentiment",
        choices=["positive", "negative", "neutral"],
        help="감정 분석 결과로 필터링합니다.",
    )

    list_parser.add_argument(
        "--rating",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="별점으로 필터링합니다.",
    )

    list_parser.add_argument(
        "--date-from",
        help="조회 시작일 (YYYY-MM-DD)",
    )

    list_parser.add_argument(
        "--date-to",
        help="조회 종료일 (YYYY-MM-DD)",
    )

    show_parser = subparsers.add_parser(
        "show",
        help="리뷰 상세 정보를 조회합니다.",
    )

    show_parser.add_argument(
        "--id",
        type=int,
        required=True,
        help="조회할 리뷰 ID",
    )

    subparsers.add_parser(
        "analyze",
        help="미분석 리뷰를 Gemini로 감정분석합니다.",
    )

    list_parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="페이지 번호 (기본값: 1)",
    )

    list_parser.add_argument(
        "--page-size",
        type=int,
        default=10,
        help="페이지당 리뷰 수 (기본값: 10)",
    )

    list_parser.add_argument(
        "--sort",
        choices=[
            "id_asc",
            "id_desc",
            "rating_asc",
            "rating_desc",
            "confidence_asc",
            "confidence_desc",
            "date_asc",
            "date_desc",
        ],
        default="id_asc",
        help="조회 결과 정렬 기준",
    )

    subparsers.add_parser(
        "stats",
        help="리뷰 통계를 조회합니다.",
    )

    args = parser.parse_args()

    # DB 테이블 확인/생성
    create_tables()

    if args.command == "import":
        import_csv(args.file)

    elif args.command == "clean":
        clean_reviews()

    elif args.command == "analyze":
        analyze_all_unanalyzed()

    elif args.command == "list":
        list_reviews(
            sentiment=args.sentiment,
            rating=args.rating,
            date_from=args.date_from,
            date_to=args.date_to,
            page=args.page,
            page_size=args.page_size,
            sort=args.sort,
        )

    elif args.command == "show":
        show_review(args.id)

    elif args.command == "stats":
        show_stats()

if __name__ == "__main__":
    main()