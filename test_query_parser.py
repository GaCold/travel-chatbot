#!/usr/bin/env python3
"""
Script test tính năng Query Parser và Chroma filtering
"""

from src.query_parser import QueryParser


def test_query_parser():
    """Test QueryParser với các câu hỏi mẫu"""
    parser = QueryParser()

    test_queries = [
        "Địa điểm du lịch miền bắc",
        "Bãi biển đẹp ở miền nam",
        "Chùa cổ miền trung",
        "Những chợ nổi tiếng ở Sài Gòn",
        "Địa điểm du lịch nổi tiếng",  # Không có metadata cụ thể
        "Núi đẹp ở Hà Nội",
        "Ẩm thực đặc sản miền bắc",
        "Bảo tàng ở Huế",
        "Hang động ở Quảng Bình",
    ]

    print("=" * 70)
    print("🧪 TEST QUERY PARSER")
    print("=" * 70)
    print()

    for i, query in enumerate(test_queries, 1):
        print(f'📝 Test {i}: "{query}"')
        parsed = parser.parse_query(query)

        print(f"   Region detected: {parsed.get('region') or 'None'}")
        print(f"   Type detected: {parsed.get('type') or 'None'}")
        print(f"   Filters: {parsed.get('filters') or 'None'}")
        print()

    print("=" * 70)
    print("✅ Test hoàn tất!")
    print("=" * 70)


if __name__ == "__main__":
    test_query_parser()
