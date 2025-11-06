import os #thao tác file + folderr
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS #lưu truy vấn vào vector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains.conversational_retrieval.base import ConversationalRetrievalChain
import shutil #dùng để xóa hội thoại

#Không gian lưu vector
vector_space_dir = os.path.join(os.getcwd(), "vector_db")
if not os.path.exists(vector_space_dir):
    os.mkdir(vector_space_dir)

st.set_page_config(page_title="Tourism", layout="centered")
st.title("Chatbot Du Lịch")

#Khởi tạo bộ nhớ tạm Streamlit (lưu lịch sử hội thoại ngắn)
if 'vectorstore' not in st.session_state:
    st.session_state['vectorstore'] = None
if 'memory' not in st.session_state:
    st.session_state['memory'] = ConversationBufferMemory(memory_key = "chat_history", return_messages=True)
if 'retriever' not in st.session_state:
    st.session_state['retriever'] = None

#Embedding Model (chuyển text thành vector số) lấy từ file PDF qua đường dẫn
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
pdf_path = os.path.join("server", "TestDL.pdf")
st.session_state['pdf_file_path'] = pdf_path

if st.session_state.get('vectorstore') is None:
    with st.spinner("Loading PDF and creating vector DB...."):
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # Tạo vectorstore
        vectorstore = FAISS.from_documents(documents, embedding_model)
        vectorstore.save_local(vector_space_dir)

        # Lưu vào session
        st.session_state['vectorstore'] = vectorstore
        st.session_state['retriever'] = vectorstore.as_retriever(search_kwargs={"k": 5})
        st.success("Vector DB Created")

llm = OllamaLLM(model="llama3.2")

if st.session_state['retriever'] is not None:
    qa_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever = st.session_state['retriever'], memory = st.session_state['memory'], return_source_documents= False)
    user_question = st.text_input("Hỏi mình một câu bất kì:", key='text')
    if user_question:
        with st.spinner("...."):
            result = qa_chain.run({"question": user_question})
            st.markdown(f"**👽:** {user_question}")
            st.markdown(f"**🤖:** {result}")

#Tạo hàm xóa dữ liệu chat
def del_vectordb(path):
    if os.path.exists(path):
        shutil.rmtree(path)

if st.button("Xóa"):
    st.session_state['memory'].clear()
    st.session_state['retriever'] = None
    st.session_state['vectorstore'] = None
    del_vectordb(vector_space_dir)
    st.success('Đã xóa lịch sử hội thoại!')

    st.rerun()
