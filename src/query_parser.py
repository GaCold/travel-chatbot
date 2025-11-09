import re
from typing import Dict, List, Optional, Tuple


class QueryParser:
    """
    Parser để trích xuất metadata từ câu hỏi,
    ĐƯỢC TỐI ƯU VÀ ĐỒNG BỘ với cấu trúc metadata của vnexpress.jsonl.
    """

    def __init__(self):

        # 1. ÁNH XẠ TYPE: Map từ khóa của user -> metadata 'type' trong JSONL
        # (Đã kiểm tra và khớp với metadata của bạn: "overview", "transport", "cost", "attraction", "food", v.v.)
        self.type_keywords_map = {
            "food": ["ăn", "ẩm thực", "món", "đặc sản", "quán", "nhà hàng"],
            "attraction": [
                "checkin",
                "tham quan",
                "chơi",
                "địa điểm du lịch",
                "cảnh đẹp",
                "đi đâu",
                "chỗ nào đẹp",
                "khám phá",
            ],  # Gộp "khám phá" vào đây
            "accommodation": [
                "lưu trú",
                "ở đâu",
                "khách sạn",
                "nhà nghỉ",
                "resort",
                "chỗ ở",
                "homestay",
            ],
            "transport": [
                "di chuyển",
                "đi lại",
                "phương tiện",
                "bắt xe",
                "đến đó thế nào",
                "đi bằng gì",
                "tàu",
                "xe khách",
                "máy bay",
            ],
            "cost": ["giá vé", "chi phí", "bao nhiêu tiền", "giá"],
            "tips": ["lưu ý", "mẹo", "kinh nghiệm", "chú ý"],
            "activity": ["hoạt động", "vui chơi", "trải nghiệm"],
            "overview": ["tổng quan", "giới thiệu", "thông tin chung", "về"],
            # Gộp "cẩm nang" vào "guide"
            "guide": ["cẩm nang", "thời tiết", "mùa nào đẹp", "nên đi khi nào"],
            "itinerary": ["lịch trình", "kế hoạch", "2 ngày", "3 ngày"],
        }

        # 2. ÁNH XẠ REGION: Map từ khóa user -> metadata 'region' trong JSONL
        # (Đã kiểm tra và khớp: "miền bắc", "miền trung", "miền nam")
        self.region_keywords_map = {
            "miền bắc": ["miền bắc", "phía bắc", "bắc bộ"],
            "miền trung": ["miền trung", "trung bộ", "duyên hải"],
            "miền nam": ["miền nam", "nam bộ", "miền tây", "đông nam bộ"],
        }

        # 3. ÁNH XẠ LOCATION: Map từ khóa user -> metadata 'location_city' và 'location_specific'
        # [QUAN TRỌNG] Danh sách này được xây dựng 100% từ file vnexpress.jsonl của bạn.
        # (Key chuẩn trong JSONL): ( (list từ khóa user), (loại key: 'location_city' hoặc 'location_specific') )

        self.location_map = {
            # ===== MIỀN BẮC (TỪ FILE JSONL) =====
            "vinh_ha_long_4626380": (
                ["vịnh hạ long", "hạ long", "halong"],
                "location_specific",
            ),
            "sa_pa_lao_cai": (["sa pa", "sapa"], "location_city"),
            "lao_cai_4697212": (["lào cai"], "location_city"),
            "meo_vac_4654320": (["mèo vạc"], "location_city"),
            "mu_cang_chai_4158151": (["mù cang chải"], "location_city"),
            "moc_chau_4098678": (["mộc châu"], "location_city"),
            "ninh_binh_4127327": (
                ["ninh bình", "tràng an", "tam cốc", "bái đính"],
                "location_city",
            ),
            "thai_nguyen_4613586": (["thái nguyên", "hồ núi cốc"], "location_city"),
            "48_gio_o_y_ty_4807822": (["y tý", "y ty"], "location_city"),
            "ta_xua_4656282": (["tà xùa"], "location_city"),
            "ha_noi_4459188": (["hà nội", "hanoi"], "location_city"),
            "ha_giang": (["hà giang"], "location_city"),
            # ===== MIỀN TRUNG (TỪ FILE JSONL) =====
            "ba_na_hills": (["bà nà", "ba na hills", "cầu vàng"], "location_specific"),
            "cu_lao_xanh_4598306": (["cù lao xanh"], "location_specific"),
            "cu_lao_cham_4751193": (["cù lao chàm"], "location_specific"),
            "ky_co_4475856": (["kỳ co"], "location_specific"),
            "lang_co_4625414": (["lăng cô"], "location_specific"),
            "mang_den_4619200": (["măng đen"], "location_specific"),
            "mui_ne_3838646": (["mũi né", "mui ne"], "location_specific"),
            "dao_phu_quy_3775534": (["phú quý", "đảo phú quý"], "location_specific"),
            "pu_luong_4153045": (["pù luông"], "location_specific"),
            "vuon_quoc_gia_pu_mat_4858184": (
                ["pù mát", "vườn quốc gia pù mát"],
                "location_specific",
            ),
            "vuon_quoc_gia_bach_ma_4817811": (
                ["bạch mã", "vườn quốc gia bạch mã"],
                "location_specific",
            ),
            "pho_co_hoi_an": (["hội an", "phố cổ hội an"], "location_specific"),
            "binh_thuan_4749039": (["bình thuận", "phan thiết"], "location_city"),
            "binh_dinh_4729689": (["bình định"], "location_city"),
            "quy_nhon_4119727": (["quy nhơn"], "location_city"),
            "binh_ba_4449076": (["bình ba"], "location_city"),
            "buon_ma_thuot_4190200": (["buôn ma thuột", "bmt"], "location_city"),
            "dak_nong_4650407": (["đăk nông", "đắk nông"], "location_city"),
            "da_nang": (["đà nẵng", "danang"], "location_city"),
            "da_lat": (["đà lạt", "dalat"], "location_city"),
            "dak_lak_4453797": (["đắk lắk", "đăk lăk"], "location_city"),
            "gia_lai_4668792": (["gia lai", "pleiku"], "location_city"),
            "ha_tinh_4742410": (["hà tĩnh"], "location_city"),
            "kon_tum_4718005": (["kon tum"], "location_city"),
            "khanh_hoa_4759133": (
                ["khánh hòa", "khánh hoà", "cam ranh"],
                "location_city",
            ),
            "nha_trang_tu_a_den_z_4127199": (["nha trang"], "location_city"),
            "ly_son_4114764": (["lý sơn", "đảo lý sơn"], "location_city"),
            "lam_dong_4807324": (["lâm đồng"], "location_city"),
            "nghe_an_4455646": (["nghệ an", "vinh"], "location_city"),
            "ninh_thuan_4453272": (["ninh thuận", "phan rang"], "location_city"),
            "phu_yen_4465949": (["phú yên", "tuy hòa", "tuy hoa"], "location_city"),
            "quang_tri_4772745": (
                ["quảng trị", "quảng bình", "đồng hới", "phong nha"],
                "location_city",
            ),
            "quang_ngai_4631099": (["quảng ngãi"], "location_city"),
            "hue_4126937": (["huế", "thừa thiên huế"], "location_city"),
            "thanh_hoa_4607348": (["thanh hóa", "thanh hoa"], "location_city"),
            "bao_loc_4643396": (["bảo lộc"], "location_city"),
            # ===== MIỀN NAM (TỪ FILE JSONL) =====
            "con_dao_4445727": (["côn đảo"], "location_specific"),
            "can_gio_4673430": (["cần giờ"], "location_specific"),
            "nam_du_4764453": (["nam du", "đảo nam du"], "location_specific"),
            "nui_dinh_diem_cam_trai_cuoi_tuan_gan_tp_hcm_4545681": (
                ["núi dinh"],
                "location_specific",
            ),
            "rung_tram_tra_su_4665214": (
                ["trà sư", "rừng tràm trà sư"],
                "location_specific",
            ),
            "goi_y_an_choi_o_pho_di_bo_nguyen_hue_4632658": (
                ["phố đi bộ nguyễn huệ"],
                "location_specific",
            ),
            "an_giang_4445399": (["an giang"], "location_city"),
            "ba_ria_vung_tau_4479713": (
                ["bà rịa - vũng tàu", "bà rịa"],
                "location_city",
            ),
            "vung_tau_4476318": (["vũng tàu"], "location_city"),
            "binh_phuoc_4667906": (["bình phước"], "location_city"),
            "binh_duong_4677956": (["bình dương"], "location_city"),
            "can_tho_3801041": (["cần thơ"], "location_city"),
            "ca_mau_4447395": (["cà mau", "mũi cà mau"], "location_city"),
            "chau_doc_4733356": (["châu đốc"], "location_city"),
            "dong_thap_4685835": (
                ["đồng tháp", "đồng tháp mười", "sa đéc"],
                "location_city",
            ),
            "dong_nai_4811218": (["đồng nai", "biên hòa"], "location_city"),
            "hcm_city": (
                ["tp hcm", "hồ chí minh", "sài gòn", "saigon"],
                "location_city",
            ),
            "phu_quoc": (["phú quốc", "đảo phú quốc"], "location_city"),
            "long_an_4796307": (["long an"], "location_city"),
            "kien_giang_4764240": (
                ["kiên giang", "rạch giá", "hà tiên"],
                "location_city",
            ),
            "tay_ninh_4795506": (["tây ninh"], "location_city"),
            "tien_giang_4799532": (["tiền giang", "mỹ tho"], "location_city"),
            "tra_vinh_4821602": (["trà vinh"], "location_city"),
        }

    def parse_query(self, question: str) -> Dict[str, any]:
        """
        Phân tích câu hỏi và trích xuất metadata (region, type, location_city, location_specific)
        """
        question_lower = question.lower()

        result = {
            "region": None,
            "type": None,
            "location_city": None,
            "location_specific": None,
            "original_query": question,
            "cleaned_query": question,
            "filters": {},
        }

        # 1. Detect Type (food, attraction, v.v.)
        detected_type = self._detect_from_map(question_lower, self.type_keywords_map)
        if detected_type:
            result["type"] = detected_type
            result["filters"]["type"] = detected_type

        # 2. Detect Region (miền bắc, miền trung, miền nam)
        detected_region = self._detect_from_map(
            question_lower, self.region_keywords_map
        )
        if detected_region:
            result["region"] = detected_region
            result["filters"]["region"] = detected_region

        # 3. Detect Location (city và specific)
        # ƯU TIÊN 1: Tìm 'location_specific' trước (ví dụ: "bà nà", "pù luông")
        detected_loc_specific = self._detect_location(
            question_lower, "location_specific"
        )
        if detected_loc_specific:
            result["location_specific"] = detected_loc_specific
            result["filters"]["location_specific"] = detected_loc_specific

        # ƯU TIÊN 2: Nếu không thấy specific, mới tìm 'location_city' (ví dụ: "đà nẵng", "hà nội")
        # Logic này ngăn việc hỏi "Bà Nà có gì chơi" chỉ trả về bài "Đà Nẵng"
        detected_loc_city = self._detect_location(question_lower, "location_city")
        if detected_loc_city:
            result["location_city"] = detected_loc_city
            # Chỉ thêm filter city NẾU CHƯA có filter specific
            if not detected_loc_specific:
                result["filters"]["location_city"] = detected_loc_city

        return result

    def _detect_from_map(
        self, text: str, keyword_map: Dict[str, List[str]]
    ) -> Optional[str]:
        """Hàm chung để detect (type, region) từ map, ưu tiên từ khóa dài nhất"""
        matches = []
        for map_key, keywords in keyword_map.items():
            for keyword in keywords:
                if keyword in text:
                    # Ưu tiên từ khóa dài hơn (khớp chính xác hơn)
                    matches.append((map_key, len(keyword)))

        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[0][0]  # Trả về map_key (ví dụ: "food", "miền bắc")
        return None

    def _detect_location(self, text: str, loc_type: str) -> Optional[str]:
        """
        Hàm detect location (city hoặc specific), ưu tiên từ khóa dài nhất
        loc_type: 'location_city' hoặc 'location_specific'
        """
        matches = []
        for map_key, (keywords, key_type) in self.location_map.items():
            if key_type == loc_type:
                for keyword in keywords:
                    # Thêm khoảng trắng để tránh khớp 1 phần (ví dụ: "hà" trong "hà giang" khớp với "hà nội")
                    # Bằng cách tìm " hà nội " hoặc "hà nội " hoặc " hà nội"
                    if re.search(r"\b" + re.escape(keyword) + r"\b", text):
                        matches.append((map_key, len(keyword)))

        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[0][
                0
            ]  # Trả về map_key chuẩn (ví dụ: "da_nang", "ba_na_hills")
        return None

    def build_filter_dict(self, parsed_query: Dict) -> Optional[Dict]:
        """
        Xây dựng filter dict cho Chroma DỰA TRÊN CÁC KEY CHUẨN (metadata)
        """
        filters = []

        # Sử dụng dict "filters" đã được xây dựng cẩn thận trong parse_query
        if parsed_query.get("filters"):
            if parsed_query["filters"].get("region"):
                filters.append({"region": {"$eq": parsed_query["filters"]["region"]}})

            if parsed_query["filters"].get("type"):
                filters.append({"type": {"$eq": parsed_query["filters"]["type"]}})

            # Ưu tiên lọc "location_specific" nếu có
            if parsed_query["filters"].get("location_specific"):
                filters.append(
                    {
                        "location_specific": {
                            "$eq": parsed_query["filters"]["location_specific"]
                        }
                    }
                )
            # Nếu không có specific, mới lọc "location_city"
            elif parsed_query["filters"].get("location_city"):
                filters.append(
                    {"location_city": {"$eq": parsed_query["filters"]["location_city"]}}
                )

        if not filters:
            return None
        if len(filters) == 1:
            return filters[0]

        return {"$and": filters}
