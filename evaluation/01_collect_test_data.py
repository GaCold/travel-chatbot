"""
Bước 1: Thu thập dữ liệu đánh giá
==================================

Script này:
1. Định nghĩa các test cases (câu hỏi)
2. Gọi chatbot để lấy câu trả lời + retrieved contexts
3. Lưu kết quả dạng RAGAS format vào file JSON

Output: evaluation/test_data.json
Format:
{
    "test_cases": [
        {
            "user_input": "Câu hỏi",
            "response": "Câu trả lời từ bot",
            "retrieved_contexts": ["Context 1", "Context 2", ...],
        },
        ...
    ]
}
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import List, Dict

# Add repo root to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.chatbot import TravelChatbot
from src.config import Config


# ===========================================================================#
#                           Test cases định sẵn                              #
# ===========================================================================#

# TEST_CASES = [
#     # Specific locations
#     {"question": "Hà Nội nên đi đâu chơi?"},
#     {"question": "Hạ Long nổi tiếng cái gì?"},
#     {"question": "Sapa có gì thú vị?"},
    
#     # Regional queries
#     {"question": "Gợi ý du lịch miền bắc"},
#     {"question": "Miền trung có những địa điểm nào?"},
#     {"question": "Điểm tham quan nổi tiếng ở miền nam"},
    
#     # Off-topic questions (should return "no data" message)
#     {"question": "Thời tiết hôm nay thế nào?"},
#     {"question": "2 + 2 bằng bao nhiêu?"},
    
#     # More specific location queries
#     {"question": "Du lịch Huế nên tham quan những nơi nào?"},
#     {"question": "Đà Nẵng có những đặc sản gì?"},
#     # -----------------------------
#     # --- Miền Bắc ---
#     # Hà Nội
#     {"question": "Hà Nội mùa nào đẹp nhất để du lịch?"},
#     {"question": "Ăn phở ở đâu ngon tại Hà Nội?"},
#     {"question": "Gợi ý mua quà gì khi đi Hà Nội?"},
#     {"question": "Các điểm tham quan lịch sử ở Hà Nội là gì?"},
#     {"question": "Giá vé xe buýt hai tầng ở Hà Nội?"},
#     # Vịnh Hạ Long
#     {"question": "Giá vé tham quan Vịnh Hạ Long tuyến 1 là bao nhiêu?"},
#     {"question": "Hòn Trống Mái ở đâu?"},
#     {"question": "Có thể ngủ đêm trên Vịnh Hạ Long không?"},
#     {"question": "Đi thủy phi cơ ngắm Vịnh Hạ Long giá bao nhiêu?"},
#     # Lào Cai (Sa Pa, Y Tý)
#     {"question": "Đi đến đỉnh Fansipan bằng cách nào?"},
#     {"question": "Ăn gì đặc sản ở Sa Pa?"},
#     {"question": "Bản Cát Cát ở đâu?"},
#     {"question": "Chợ phiên Bắc Hà họp ngày nào?"},
#     {"question": "Đi Y Tý mùa nào đẹp nhất để săn mây?"},
#     {"question": "Cột cờ Lũng Pô ở đâu?"},
#     # Hà Giang (Mèo Vạc)
#     {"question": "Đèo Mã Pì Lèng thuộc tỉnh nào?"},
#     {"question": "Đi thuyền trên sông Nho Quế giá bao nhiêu?"},
#     {"question": "Chợ tình Khâu Vai họp khi nào?"},
#     # Mù Cang Chải
#     {"question": "Mù Cang Chải mùa lúa chín tháng mấy?"},
#     {"question": "Đồi Mâm Xôi ở đâu?"},
#     {"question": "Lễ hội Bay trên mùa vàng tổ chức ở đâu?"},
#     # Mộc Châu
#     {"question": "Mộc Châu có hoa gì vào tháng 1?"},
#     {"question": "Thác Chiềng Khoa ở đâu?"},
#     {"question": "Đặc sản Mộc Châu là gì?"},
#     # Ninh Bình
#     {"question": "Đi thuyền ở Tràng An có mấy tuyến?"},
#     {"question": "Đặc sản Ninh Bình là gì?"},
#     {"question": "Leo Hang Múa có bao nhiêu bậc thang?"},
#     {"question": "Vườn quốc gia Cúc Phương thuộc tỉnh nào?"},
#     # Thái Nguyên
#     {"question": "Hồ Núi Cốc có gì chơi?"},
#     {"question": "Khu di tích ATK Định Hóa ở đâu?"},
    
#     # --- Miền Trung ---
#     # Thanh Hóa (Pù Luông)
#     {"question": "Pù Luông mùa lúa chín vào tháng mấy?"},
#     {"question": "Đặc sản Pù Luông là gì?"},
#     {"question": "Thành nhà Hồ ở đâu?"},
#     {"question": "Suối cá thần Cẩm Lương ở đâu?"},
#     # Nghệ An
#     {"question": "Nên đi Nghệ An mùa nào?"},
#     {"question": "Vườn quốc gia Pù Mát có gì?"},
#     {"question": "Tham quan đảo chè Thanh Chương như thế nào?"},
#     # Hà Tĩnh
#     {"question": "Biển Thiên Cầm ở đâu?"},
#     {"question": "Đặc sản Hà Tĩnh là gì?"},
#     {"question": "Khu di tích Ngã ba Đồng Lộc thuộc huyện nào?"},
#     # Quảng Trị
#     {"question": "Cầu Hiền Lương bắc qua sông nào?"},
#     {"question": "Địa đạo Vịnh Mốc ở đâu?"},
#     {"question": "Các di tích lịch sử nổi tiếng ở Quảng Trị?"},
#     # Huế & Lăng Cô
#     {"question": "Đi Huế mùa nào đẹp nhất?"},
#     {"question": "Ăn gì ngon ở Huế?"},
#     {"question": "Kể tên các lăng tẩm triều Nguyễn ở Huế?"},
#     {"question": "Vịnh Lăng Cô có gì đẹp?"},
#     # Đà Nẵng & Bà Nà
#     {"question": "Di chuyển đến Bà Nà Hills như thế nào?"},
#     {"question": "Giá vé cáp treo Bà Nà Hills bao nhiêu?"},
#     {"question": "Cầu Vàng nằm ở đâu?"},
#     {"question": "Đà Nẵng có những cây cầu nổi tiếng nào?"},
#     {"question": "Ăn gì ở Đà Nẵng?"},
#     # Quảng Nam (Hội An, Cù Lao Chàm)
#     {"question": "Phố cổ Hội An có gì chơi?"},
#     {"question": "Ăn gì đặc sản ở Hội An?"},
#     {"question": "Đi Cù Lao Chàm bằng cách nào?"},
#     {"question": "Đặc sản Cù Lao Chàm là gì?"},
#     # Quảng Ngãi (Lý Sơn)
#     {"question": "Nên đi Lý Sơn vào tháng mấy?"},
#     {"question": "Đi ra đảo Lý Sơn bằng phương tiện gì?"},
#     {"question": "Đặc sản Quảng Ngãi là gì?"},
#     # Bình Định (Quy Nhơn, Kỳ Co, Cù Lao Xanh)
#     {"question": "Quy Nhơn có gì chơi?"},
#     {"question": "Đặc sản Bình Định là gì?"},
#     {"question": "Làm thế nào để đến Kỳ Co?"},
#     {"question": "Eo Gió ở đâu?"},
#     # Phú Yên
#     {"question": "Gành Đá Đĩa ở đâu?"},
#     {"question": "Đặc sản Phú Yên là gì?"},
#     {"question": "Mũi Điện (Mũi Đại Lãnh) ở đâu?"},
#     # Khánh Hòa (Nha Trang, Bình Ba)
#     {"question": "Nha Trang có những điểm tham quan nào?"},
#     {"question": "Ăn gì ngon ở Nha Trang?"},
#     {"question": "Đặc sản của đảo Bình Ba là gì?"},
#     {"question": "Thời điểm lý tưởng để đi Bình Ba?"},
#     # Ninh Thuận
#     {"question": "Vịnh Vĩnh Hy ở đâu?"},
#     {"question": "Đặc sản Ninh Thuận là gì?"},
#     {"question": "Có thể tham quan vườn nho ở Ninh Thuận không?"},
#     # Bình Thuận (Mũi Né, Phan Thiết, Phú Quý)
#     {"question": "Mũi Né có gì chơi?"},
#     {"question": "Đặc sản Phan Thiết là gì?"},
#     {"question": "Đi đảo Phú Quý bằng cách nào?"},
#     {"question": "Ăn gì ở đảo Phú Quý?"},

#     # --- Tây Nguyên ---
#     # Đắk Lắk & Buôn Ma Thuột
#     {"question": "Buôn Ma Thuột mùa nào đẹp?"},
#     {"question": "Ăn gì ở Buôn Ma Thuột?"},
#     {"question": "Bảo tàng Thế giới Cà phê ở đâu?"},
#     # Đắk Nông
#     {"question": "Hồ Tà Đùng ở đâu?"},
#     {"question": "Đặc sản Đắk Nông là gì?"},
#     # Gia Lai
#     {"question": "Gia Lai có gì chơi?"},
#     {"question": "Phở hai tô ở Gia Lai là gì?"},
#     # Kon Tum & Măng Đen
#     {"question": "Măng Đen mùa nào đẹp?"},
#     {"question": "Nhà thờ gỗ Kon Tum xây dựng năm nào?"},
#     {"question": "Ăn gì ở Măng Đen?"},
#     # Lâm Đồng & Đà Lạt
#     {"question": "Đà Lạt mùa nào đẹp?"},
#     {"question": "Ăn gì đặc sản ở Đà Lạt?"},
#     {"question": "Vườn quốc gia Bidoup - Núi Bà ở đâu?"},

#     # --- Miền Nam ---
#     # TP HCM & Cần Giờ
#     {"question": "TP HCM có gì chơi?"},
#     {"question": "Ăn gì ngon ở TP HCM?"},
#     {"question": "Chợ Bến Thành ở đâu?"},
#     {"question": "Đi Cần Giờ bằng cách nào?"},
#     # An Giang (Châu Đốc, Trà Sư)
#     {"question": "Rừng tràm Trà Sư mùa nào đẹp nhất?"},
#     {"question": "Ăn gì ở Châu Đốc?"},
#     {"question": "Miếu Bà Chúa Xứ núi Sam ở đâu?"},
#     # Bà Rịa - Vũng Tàu & Côn Đảo
#     {"question": "Vũng Tàu có bãi biển nào đẹp?"},
#     {"question": "Ăn gì ở Vũng Tàu?"},
#     {"question": "Đi Côn Đảo mùa nào đẹp?"},
#     {"question": "Nhà tù Côn Đảo ở đâu?"},
#     {"question": "Núi Dinh có gì chơi?"},
#     # Bình Phước
#     {"question": "Vườn quốc gia Bù Gia Mập ở đâu?"},
#     {"question": "Đặc sản Bình Phước là gì?"},
#     # Bình Dương
#     {"question": "Khu du lịch Đại Nam ở đâu?"},
#     {"question": "Đặc sản Bình Dương là gì?"},
#     # Cần Thơ
#     {"question": "Chợ nổi Cái Răng họp lúc mấy giờ?"},
#     {"question": "Ăn gì ở Cần Thơ?"},
#     {"question": "Nhà cổ Bình Thủy ở đâu?"},
#     # Đồng Tháp
#     {"question": "Vườn quốc gia Tràm Chim có gì đặc biệt?"},
#     {"question": "Làng hoa Sa Đéc ở đâu?"},
#     # Đồng Nai
#     {"question": "Hồ Trị An có gì chơi?"},
#     {"question": "Vườn quốc gia Cát Tiên thuộc tỉnh nào?"},
#     # Tây Ninh
#     {"question": "Núi Bà Đen cao bao nhiêu?"},
#     {"question": "Tòa thánh Tây Ninh của đạo nào?"},
#     {"question": "Đặc sản Tây Ninh là gì?"},
#     # Tiền Giang
#     {"question": "Chùa Vĩnh Tràng ở đâu?"},
#     {"question": "Hủ tiếu Mỹ Tho có gì đặc biệt?"},
#     # Trà Vinh
#     {"question": "Ao Bà Om ở đâu?"},
#     {"question": "Đặc sản Trà Vinh là gì?"},

#     # --- Câu hỏi theo khu vực (như trong ví dụ) ---
#     {"question": "Gợi ý du lịch miền Bắc"},
#     {"question": "Miền Trung có những địa điểm nào?"},
#     {"question": "Điểm tham quan nổi tiếng ở miền Nam"},
#     {"question": "Đặc sản miền Tây là gì?"},
#     {"question": "Những bãi biển đẹp ở miền Trung?"},
#     {"question": "Tây Nguyên có gì chơi?"},

#     # --- Câu hỏi ngoài chủ đề (Off-topic - như trong ví dụ) ---
#     {"question": "Thời tiết ngày mai thế nào?"},
#     {"question": "Tổng thống Mỹ là ai?"},
#     {"question": "Viết cho tôi một bài thơ về mùa hè"},
#     {"question": "Công thức nấu ăn phở bò?"},
#     {"question": "Giá vàng hôm nay bao nhiêu?"},
#     {"question": "Lịch sử chiến tranh Việt Nam?"},
#     {"question": "Đặt vé máy bay đi Đà Nẵng"},
#     {"question": "Covid-19 là gì?"},

#     # --- Câu hỏi so sánh / phức tạp ---
#     {"question": "Nên đi Mù Cang Chải hay Sa Pa vào tháng 9?"},
#     {"question": "So sánh Vịnh Hạ Long và Vịnh Vĩnh Hy?"},
#     {"question": "Điểm khác biệt giữa phở Hà Nội và phở hai tô Gia Lai?"},
#     {"question": "Bãi biển nào đẹp nhất miền Trung?"},
#     {"question": "Gợi ý lịch trình 3 ngày ở Huế và Đà Nẵng."},
#     {"question": "Chùa nào có tượng Phật nằm dài nhất?"},
#     {"question": "Ăn gì ở Đà Lạt và Buôn Ma Thuột?"},
#     {"question": "Nên đi Côn Đảo vào mùa nào?"},
#     {"question": "So sánh đặc sản Ninh Bình và Thanh Hóa."},
#     {"question": "Lịch trình du lịch 5 ngày ở Tây Nguyên."},

#     # --- 10 Off-Topic Questions (Bổ sung) ---
#     {"question": "Công thức nấu món bún bò Huế?"},
#     {"question": "Giá vàng hôm nay bao nhiêu?"},
#     {"question": "Viết cho tôi một bài thơ về biển Cửa Lò."},
#     {"question": "Tổng thống Mỹ hiện tại là ai?"},
#     {"question": "Làm thế nào để đặt vé máy bay đi Phú Quốc?"},
#     {"question": "Du lịch Sóc Trăng có gì hay?"},
#     {"question": "Thủ đô của nước Pháp là gì?"},
#     {"question": "Tôi bị đau bụng nên uống thuốc gì?"},
#     {"question": "Giải phương trình bậc hai: x^2 + 2x - 3 = 0"},
#     {"question": "Kể cho tôi một câu chuyện cười."}
# ]

TEST_CASES = [
    # -------------------------
    # Specific locations (50)
    # -------------------------
    {"question": "Hà Nội có gì chơi?"},
    {"question": "Ăn phở ở đâu ngon tại Hà Nội?"},
    {"question": "Giá vé xe buýt hai tầng Hà Nội bao nhiêu?"},
    {"question": "Vịnh Hạ Long nổi tiếng với gì?"},
    {"question": "Đi thủy phi cơ ngắm Vịnh Hạ Long giá bao nhiêu?"},
    {"question": "Hòn Trống Mái ở đâu?"},
    {"question": "Đà Nẵng có những cây cầu nổi tiếng nào?"},
    {"question": "Ăn gì ngon ở Đà Nẵng?"},
    {"question": "Cầu Vàng nằm ở đâu?"},
    {"question": "Giá vé cáp treo Bà Nà Hills bao nhiêu?"},
    {"question": "Phố cổ Hội An có gì chơi?"},
    {"question": "Đặc sản Hội An là gì?"},
    {"question": "Nên đi Lý Sơn vào tháng mấy?"},
    {"question": "Đi Cù Lao Chàm bằng cách nào?"},
    {"question": "Đặc sản Phú Quốc là gì?"},
    {"question": "Mũi Né có gì chơi?"},
    {"question": "Vịnh Vĩnh Hy ở đâu?"},
    {"question": "Thác Chiềng Khoa ở đâu?"},
    {"question": "Bản Cát Cát ở đâu?"},
    {"question": "Đi Y Tý mùa nào đẹp nhất?"},
    {"question": "Điểm tham quan nổi tiếng ở Mộc Châu?"},
    {"question": "Ăn gì đặc sản ở Sa Pa?"},
    {"question": "Chợ tình Khâu Vai họp khi nào?"},
    {"question": "Giá vé tham quan Tràng An tuyến 1 là bao nhiêu?"},
    {"question": "Leo Hang Múa có bao nhiêu bậc thang?"},
    {"question": "Vườn quốc gia Cúc Phương thuộc tỉnh nào?"},
    {"question": "Hồ Tà Đùng ở đâu?"},
    {"question": "Bảo tàng Thế giới Cà phê ở đâu?"},
    {"question": "Nên đi Nghệ An mùa nào?"},
    {"question": "Vườn quốc gia Pù Mát có gì?"},
    {"question": "Đặc sản Ninh Thuận là gì?"},
    {"question": "Đặc sản Ninh Bình là gì?"},
    {"question": "Làm thế nào để đến Eo Gió?"},
    {"question": "Điện Biên có gì chơi?"},
    {"question": "Đèo Mã Pì Lèng thuộc tỉnh nào?"},
    {"question": "Đi thuyền trên sông Nho Quế giá bao nhiêu?"},
    {"question": "Cầu Hiền Lương bắc qua sông nào?"},
    {"question": "Địa đạo Vịnh Mốc ở đâu?"},
    {"question": "Nhà tù Côn Đảo ở đâu?"},
    {"question": "Vườn quốc gia Bù Gia Mập ở đâu?"},
    {"question": "Chợ nổi Cái Răng họp lúc mấy giờ?"},
    {"question": "Miếu Bà Chúa Xứ núi Sam ở đâu?"},
    {"question": "Khu du lịch Đại Nam ở đâu?"},
    {"question": "Thác Datanla ở đâu?"},
    {"question": "Nhà thờ gỗ Kon Tum có gì đặc biệt?"},
    {"question": "Ăn gì đặc sản ở Đà Lạt?"},
    {"question": "Chợ Bến Thành ở đâu?"},
    {"question": "Đặc sản Châu Đốc là gì?"},
    {"question": "Đi Cần Giờ bằng cách nào?"},
    {"question": "Nhà cổ Bình Thủy ở đâu?"},

    # -------------------------
    # Regional queries (15)
    # -------------------------
    {"question": "Gợi ý du lịch miền bắc"},
    {"question": "Miền trung có những địa điểm nào?"},
    {"question": "Điểm tham quan nổi tiếng ở miền nam"},
    {"question": "Gợi ý quà đặc sản miền Tây"},
    {"question": "Đặc sản miền Trung là gì?"},
    {"question": "Các bãi biển đẹp ở miền Trung?"},
    {"question": "Tây Nguyên có gì chơi?"},
    {"question": "Các tỉnh miền Đông Nam Bộ có gì đặc biệt?"},
    {"question": "Địa điểm check-in đẹp ở miền Bắc"},
    {"question": "Miền Tây nên đi đâu vào mùa nước nổi?"},
    {"question": "Miền Trung tháng 3 có gì đẹp?"},
    {"question": "Các địa điểm du lịch lễ hội miền Bắc?"},
    {"question": "Vùng núi Tây Bắc nên đi đâu?"},
    {"question": "Du lịch miền Nam vào tháng 12 có gì?"},
    {"question": "Miền Bắc có món ăn gì ngon?"},

    # -------------------------
    # Complex queries (10)
    # -------------------------
    {"question": "Nên đi Mù Cang Chải hay Sa Pa vào tháng 9?"},
    {"question": "So sánh Vịnh Hạ Long và Vịnh Vĩnh Hy?"},
    {"question": "So sánh đặc sản Ninh Bình và Thanh Hóa."},
    {"question": "Đà Nẵng hay Nha Trang đáng đi hơn?"},
    {"question": "Cần Thơ và Cà Mau nên đi nơi nào trước?"},
    {"question": "So sánh phở Hà Nội và phở hai tô Gia Lai"},
    {"question": "Chợ nổi Cái Răng và Trà Sư, nên đi đâu trước?"},
    {"question": "Huế hay Hội An phù hợp cho nghỉ dưỡng dài ngày?"},
    {"question": "Bãi biển nào đẹp nhất miền Trung?"},
    {"question": "Phú Quốc hay Côn Đảo đẹp hơn?"},

    # -------------------------
    # Off-topic (15)
    # -------------------------
    {"question": "Thời tiết hôm nay thế nào?"},
    {"question": "Giá vàng hôm nay bao nhiêu?"},
    {"question": "Viết cho tôi một bài thơ về biển Cửa Lò."},
    {"question": "Tổng thống Mỹ là ai?"},
    {"question": "Làm thế nào để đặt vé máy bay đi Phú Quốc?"},
    {"question": "Công thức nấu món bún bò Huế?"},
    {"question": "Thủ đô của nước Pháp là gì?"},
    {"question": "Tôi bị đau bụng nên uống thuốc gì?"},
    {"question": "Kể cho tôi một câu chuyện cười."},
    {"question": "Tại sao mặt trời mọc ở hướng Đông?"},
    {"question": "Covid-19 là gì?"},
    {"question": "Giải phương trình x^2 + 2x - 3 = 0"},
    {"question": "Làm sao để viết một bài luận?"},
    {"question": "Tắt thông báo email trên iPhone?"},
    {"question": "Có bao nhiêu hành tinh trong hệ mặt trời?"},

    # -------------------------
    # Itinerary / Synthesis (10)
    # -------------------------
    {"question": "Gợi ý lịch trình 3 ngày ở Huế và Đà Nẵng."},
    {"question": "Đi Đà Lạt 2 ngày nên đi đâu?"},
    {"question": "Lịch trình 4 ngày ở miền Tây nên đi tỉnh nào?"},
    {"question": "Gợi ý tour 5 ngày ở Tây Nguyên."},
    {"question": "Du lịch miền Trung 3 ngày nên đi Đà Nẵng hay Huế?"},
    {"question": "Lịch trình phượt xe máy từ Hà Nội đi Hà Giang."},
    {"question": "Làm gì trong 1 ngày ở Cần Thơ?"},
    {"question": "Lịch trình 2 ngày ở Ninh Bình."},
    {"question": "Hà Nội – Sa Pa 2 ngày nên đi đâu?"},
    {"question": "Du lịch tự túc Quảng Bình 3 ngày đi đâu?"}
]


async def collect_test_data(output_file: str = "evaluation/test_data.json"):
    """
    Thu thập dữ liệu từ chatbot
    
    Args:
        output_file: Path để lưu JSON output
    """
    
    print("\n" + "="*70)
    print("📊 BƯỚC 1: THU THẬP DỮ LIỆU ĐÁNH GIÁ")
    print("="*70)
    
    # Khởi tạo chatbot
    print("\n🤖 Khởi tạo chatbot...")
    print(f"   LLM Model: {Config.LLM_MODEL}")
    print(f"   Embedding Model: {Config.EMBEDDING_MODEL_NAME} ({Config.EMBEDDING_MODEL_TYPE})")
    print(f"   Persist Directory: {Config.PERSIST_DIRECTORY}")
    try:
        config = Config()
        chatbot = TravelChatbot(
            llm_model=config.LLM_MODEL,
            embedding_model_name=config.EMBEDDING_MODEL_NAME,
            embedding_model_type=config.EMBEDDING_MODEL_TYPE,
            persist_directory=config.PERSIST_DIRECTORY
        )
        
        if not chatbot.load_existing_vector_store():
            print("❌ Không thể tải vector store")
            return False
        
        print("✅ Chatbot initialized")
    
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Thu thập dữ liệu cho mỗi test case
    collected_data = []
    
    print(f"\n📝 Processing {len(TEST_CASES)} test cases...")
    print("-" * 70)
    
    for idx, test_case in enumerate(TEST_CASES, 1):
        question = test_case["question"]
        print(f"\n[{idx}/{len(TEST_CASES)}] Question: {question}")
        
        try:
            # Lấy retrieved contexts (documents)
            docs = chatbot._get_relevant_docs(question)
            retrieved_contexts = [doc.page_content for doc in docs] if docs else []
            
            print(f"  📚 Retrieved {len(retrieved_contexts)} contexts")
            
            # Lấy response từ chatbot
            qa_result = await chatbot.ask_question(question)
            response = qa_result["answer"]
            
            print(f"  ✅ Got response (length: {len(response)} chars)")
            print(f"  Response preview: {response[:100]}...")
            
            # Tạo sample cho RAGAS format
            sample = {
                "user_input": question,
                "response": response,
                "retrieved_contexts": retrieved_contexts,
            }
            
            collected_data.append(sample)
            print(f"  ✓ Data collected")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            # Skip this case nhưng tiếp tục
            continue
    
    print("\n" + "-" * 70)
    print(f"✅ Collected {len(collected_data)}/{len(TEST_CASES)} test cases")
    
    # Lưu vào file JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    output_data = {
        "test_cases": collected_data,
        "total": len(collected_data),
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Saved to: {output_path}")
        print(f"   File size: {output_path.stat().st_size} bytes")
        return True
    
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False


async def main():
    success = await collect_test_data()
    
    if success:
        print("\n" + "="*70)
        print("✅ Bước 1 hoàn thành! File test_data.json đã được tạo.")
        print("   Bước tiếp theo: python evaluation/02_run_ragas_evaluation.py")
        print("="*70 + "\n")
    else:
        print("\n❌ Bước 1 thất bại!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
