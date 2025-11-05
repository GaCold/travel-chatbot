"""
Query Parser - Trích xuất metadata từ câu hỏi người dùng
Giúp tối ưu hóa truy vấn bằng cách phát hiện vùng miền, loại địa điểm từ câu hỏi
"""

import re
from typing import Dict, Optional, List


class QueryParser:
    """Parser để trích xuất metadata từ câu hỏi"""

    def __init__(self):
        # Mapping các từ khóa vùng miền
        self.region_keywords = {
            "miền bắc": [
                "miền bắc",
                "bắc bộ",
                "phía bắc",
                "hà nội",
                "sapa",
                "hạ long",
                "ninh bình",
            ],
            "miền trung": [
                "miền trung",
                "trung bộ",
                "phía trung",
                "huế",
                "đà nẵng",
                "hội an",
                "nha trang",
                "quy nhơn",
                "quảng bình",
            ],
            "miền nam": [
                "miền nam",
                "nam bộ",
                "phía nam",
                "sài gòn",
                "tp.hcm",
                "tp hcm",
                "hồ chí minh",
                "vũng tàu",
                "đà lạt",
                "phú quốc",
                "cần thơ",
                "mỹ tho",
            ],
        }

        # Mapping các từ khóa loại địa điểm
        self.type_keywords = {
            "chợ": ["chợ", "market"],
            "bảo tàng": ["bảo tàng", "museum"],
            "đình": ["đình", "chùa", "đền", "miếu", "temple"],
            "công viên": ["công viên", "park", "vườn"],
            "biển": ["biển", "bãi biển", "beach", "bờ biển"],
            "núi": ["núi", "đỉnh", "mountain"],
            "thác": ["thác", "thác nước", "waterfall"],
            "hang động": ["hang", "động", "cave"],
            "di sản": ["di sản", "heritage", "unesco"],
            "ẩm thực": ["ăn", "ẩm thực", "món", "đặc sản", "quán", "nhà hàng"],
            "lễ hội": ["lễ hội", "festival", "sự kiện"],
        }

    def parse_query(self, question: str) -> Dict[str, any]:
        """
        Phân tích câu hỏi và trích xuất metadata

        Args:
            question: Câu hỏi từ người dùng

        Returns:
            Dict chứa:
                - region: Vùng miền được phát hiện (nếu có)
                - type: Loại địa điểm được phát hiện (nếu có)
                - original_query: Câu hỏi gốc
                - cleaned_query: Câu hỏi đã làm sạch (có thể dùng cho embedding)
        """
        question_lower = question.lower()

        result = {
            "region": None,
            "type": None,
            "original_query": question,
            "cleaned_query": question,
            "filters": {},
        }

        # Detect region
        detected_region = self._detect_region(question_lower)
        if detected_region:
            result["region"] = detected_region
            result["filters"]["region"] = detected_region

        # Detect type
        detected_type = self._detect_type(question_lower)
        if detected_type:
            result["type"] = detected_type
            result["filters"]["type"] = detected_type

        return result

    def _detect_region(self, text: str) -> Optional[str]:
        """Phát hiện vùng miền từ text - ưu tiên từ khóa dài hơn"""
        # Sắp xếp theo độ dài keywords giảm dần để ưu tiên khớp chính xác
        matches = []
        for region, keywords in self.region_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    matches.append((region, len(keyword)))

        # Trả về region với keyword dài nhất (chính xác nhất)
        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[0][0]
        return None

    def _detect_type(self, text: str) -> Optional[str]:
        """Phát hiện loại địa điểm từ text"""
        for place_type, keywords in self.type_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return place_type
        return None

    def build_filter_dict(self, parsed_query: Dict) -> Dict:
        """
        Xây dựng filter dict cho Chroma

        Args:
            parsed_query: Kết quả từ parse_query()

        Returns:
            Dict filter theo định dạng Chroma where clause
        """
        filters = {}

        if parsed_query.get("region"):
            filters["region"] = parsed_query["region"]

        if parsed_query.get("type"):
            filters["type"] = parsed_query["type"]

        return filters if filters else None

    def enhance_query_for_embedding(self, parsed_query: Dict) -> str:
        """
        Tăng cường câu hỏi để embedding tốt hơn
        Nối metadata vào câu hỏi nếu có
        """
        query = parsed_query["original_query"]

        # Nếu có metadata, có thể nối vào (tuỳ chọn)
        # enhancements = []
        # if parsed_query.get("region"):
        #     enhancements.append(parsed_query["region"])
        # if parsed_query.get("type"):
        #     enhancements.append(parsed_query["type"])

        # if enhancements:
        #     query = " ".join(enhancements) + " " + query

        return query
