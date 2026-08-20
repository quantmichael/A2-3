import argparse

from database import create_tables
from importer import import_csv
from cleaner import clean_reviews
from analyzer import analyze_all_unanalyzed


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
    # analyze
    # -------------------------
    subparsers.add_parser(
        "analyze",
        help="미분석 리뷰를 Gemini로 감정분석합니다.",
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


if __name__ == "__main__":
    main()