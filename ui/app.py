import streamlit as st
import base64
import os

# Thử import bot thật, fallback demo
try:
    from server.agentic_chatbot import AgenticRAGChatbot as RealBot
    USE_REAL_BOT = True
except Exception:
    USE_REAL_BOT = False

if USE_REAL_BOT:
    try:
        bot = RealBot(jsonl_file_path="server/travel.jsonl", model_name="llama3.2")
        bot.initialize()
    except Exception as e:
        st.warning(f"⚠️ Không thể khởi tạo bot thật: {e}")
        USE_REAL_BOT = False

if not USE_REAL_BOT:
    class AgenticRAGChatbot:
        def ask(self, prompt):
            if "Hà Nội" in prompt:
                return {"answer": "🏯 Hà Nội là thủ đô của Việt Nam, nổi tiếng với Hồ Hoàn Kiếm, Văn Miếu và 36 phố phường."}
            elif "Huế" in prompt:
                return {"answer": "🏰 Huế là cố đô của Việt Nam, nổi tiếng với Kinh Thành Huế và các lăng tẩm vua Nguyễn."}
            elif "Đà Nẵng" in prompt:
                return {"answer": "🌉 Đà Nẵng có Cầu Rồng, Bà Nà Hills và bãi biển Mỹ Khê tuyệt đẹp!"}
            else:
                return {"answer": f"🤖 Mình chưa có dữ liệu về '{prompt}', nhưng mình đang học thêm nhé!"}

    bot = AgenticRAGChatbot()

def add_bg_from_local(image_file):
    abs_path = os.path.join(os.getcwd(), image_file)
    with open(abs_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: white;
        }}
        
        /*USER*/
        .stChatMessage:nth-child(odd) div[data-testid="stChatMessageContent"] {{
            background-color: rgba(105, 166, 65, 0.85) !important; /* Xanh dương mờ */
            color: white !important;
            border-radius: 12px !important;
            padding: 10px !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.4);
        }}
        .stChatMessage:nth-child(odd) div[data-testid="stChatMessageContent"] p {{
            background-color: transparent !important;
            color: white !important;
        }}

        /*ASSISTANT/BOT*/
        .stChatMessage:nth-child(even) div[data-testid="stChatMessageContent"] {{
            background-color: rgba(255, 127, 14, 0.85) !important; /* Cam mờ */
            color: white !important;
            border-radius: 12px !important;
            padding: 10px !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.4);
        }}
        .stChatMessage:nth-child(even) div[data-testid="stChatMessageContent"] p {{
            background-color: transparent !important;
            color: white !important;
        }}


        /*XÓA NỀN MẶT ĐỊNH STREAMLIT*/
        .stChatMessage {{
            background-color: transparent !important;
        }}
        .stChatMessage > div {{
            background-color: transparent !important;
        }}
        
        /*Input*/
        .stTextInput > div > div > input {{
            background: rgba(255,255,255) !important; 
            color: black !important;
            border-radius: 8px !important;
            padding: 10px !important;
        }}

        /*CHATBOT/
        .st-emotion-cache-1dp5yy6 {{
            background-color: rgba(0,0,0); 
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .st-emotion-cache-1dp5yy6 h1 {{
            color: white !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

add_bg_from_local("ui/app.jpg")

st.title("Chatbot du lịch Việt Nam")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

prompt = st.chat_input("Nhập câu hỏi của bạn về du lịch Việt Nam...")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    result = bot.ask(prompt)
    answer = result["answer"]

    st.chat_message("assistant").markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
