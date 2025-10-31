import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server.agentic_chatbot import AgenticRAGChatbot

import streamlit as st
from typing import Literal
from dataclasses import dataclass

JSONL_FILE = "server/travel.jsonl"
MODEL_NAME = "llama3.2"

@dataclass
class Message:
    origin: Literal["human","ai"]
    message: str
#Memory: Lưu lịch sử chat
class ConversationMemory:
    def __init__(self, max_turns=10):
        self.history = []
        self.max_turns = max_turns
    
    def add_user(self, text):
        self.history.append(f"Bạn: {text}")
        self._truncate()
    
    def add_ai(self, text):
        self.history.append(f"Bot: {text}")
        self._truncate()
    
    def get_context(self):
        return "\n".join(self.history)
    
    def _truncate(self):
        if len(self.history) > self.max_turns*2:  # 2 entries per turn
            self.history = self.history[-self.max_turns*2:]

memory = ConversationMemory(max_turns=5)

#lưu trữ chat (user - bot) sau mỗi lần submit
def initialize_session_state():
    if "history" not in st.session_state:
        st.session_state.history = [] #bộ nhớ tạm dạng từ điển
        st.session_state.history.append({"origin": "user", "message": "Hello"})

    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    if "token_count" not in st.session_state:
        st.session_state.token_count = 0

    if "llm" not in st.session_state:
        llm = AgenticRAGChatbot(JSONL_FILE, MODEL_NAME)
        llm.initialize()  # cực kỳ quan trọng, để build graph
        st.session_state.llm = llm

def load_css():
    with open("ui/static/style.css", "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

def on_click_callback():
    human_prompt = st.session_state.human_prompt
    
    # Gọi LLM để nhận phản hồi
    llm_response_dict = st.session_state.llm.ask(human_prompt)
    llm_response = llm_response_dict["answer"]
    
    # Lưu lịch sử để hiển thị
    # Lưu lịch sử để hiển thị
    st.session_state.history.append({"origin": "user", "message": human_prompt})
    st.session_state.history.append({"origin": "ai", "message": llm_response})

    
    # Lưu vào conversation nếu bạn muốn giữ record
    st.session_state.conversation.append({"user": human_prompt, "ai": llm_response})


load_css()
initialize_session_state() #đảm bảo bộ nhớ tạm luôn tồn tại, hoạt động

# tiêu đề trang #
st.title("Chatbot du lịch")

chat_placeholder = st.container()   #vùng chứa lưu trữ lịch sử trò chuyện
prompt_placeholder = st.form("chat-form") #form nhập liệu (chỉ gửi khi nhấn submit)
credit_card_placeholder = st.empty() #tạo vùng trống

bot_url = "https://cdn-icons-png.flaticon.com/512/4712/4712109.png"
user_url = "https://cdn-icons-png.flaticon.com/512/847/847969.png"

with chat_placeholder:
    for chat in st.session_state.history:
        img_url = bot_url if chat["origin"] == "ai" else user_url
        div = f"""
        <div class="chat-row {'row-reverse' if chat['origin']=='user' else ''}">
            <img class="chat-icon" src="{img_url}" width="32" height="32">
            <div class="chat-bubble {'ai-bubble' if chat['origin']=='ai' else 'human-bubble'}">
            &#8203; {chat["message"]}</div>
        </div>
        """
        st.markdown(div,unsafe_allow_html=True)

#định dạng form nhập liệu
with prompt_placeholder:
    st.markdown("**Chat** - _Nhấn Enter để Gửi yêu cầu_")
    cols = st.columns((6,1)) #tỉ lệ 6:1 (khung chat:submit)
    cols[0].text_input(
        "Chat",
        value = "hello bot",
        label_visibility = "collapsed",
        key = "human_prompt",
    )
    cols[1].form_submit_button(
        "Submit",
        type = "primary",
        on_click = on_click_callback,
    )
