import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
from newspaper import Article

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# 🔐 Groq API Key
os.environ["GROQ_API_KEY"] = ""

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

st.set_page_config(page_title="AI News Summarizer", page_icon="📰", layout="wide")

st.title("📰 AI News Article Summarizer")
st.caption("Smart AI-powered summarization with customizable output.")

# ---------------- SIDEBAR SETTINGS ---------------- #

st.sidebar.header("⚙️ Summary Settings")

summary_style = st.sidebar.selectbox(
    "Summary Format",
    ["Bullet Points", "Paragraph", "Detailed Analysis"]
)

bullet_count = st.sidebar.slider(
    "Number of Bullet Points",
    min_value=3,
    max_value=10,
    value=5
)

summary_length = st.sidebar.selectbox(
    "Summary Length",
    ["Short", "Medium", "Long"]
)

temperature = st.sidebar.slider(
    "Creativity Level",
    min_value=0.0,
    max_value=1.0,
    value=0.0
)

# Update model temperature dynamically
llm.temperature = temperature

# ---------------- URL INPUT ---------------- #

url = st.text_input("🔗 Enter News Article URL")

# ---------------- ARTICLE EXTRACTION ---------------- #

def extract_article(url):
    try:
        # Try newspaper first
        article = Article(url, browser_user_agent="Mozilla/5.0")
        article.download()
        article.parse()
        if len(article.text) > 500:
            return article.title, article.text
    except:
        pass

    # Fallback method
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.string if soup.title else "No Title Found"

    paragraphs = soup.find_all("p")

    clean_paragraphs = []

    for p in paragraphs:
        text = p.get_text().strip()
        if len(text) > 50:  # filter junk
            clean_paragraphs.append(text)

    text = " ".join(clean_paragraphs)

    return title, text

# ---------------- GENERATE BUTTON ---------------- #

if st.button("🚀 Generate Summary"):

    if not url:
        st.warning("Please enter a valid URL.")
    else:
        try:
            with st.spinner("🔍 Extracting article..."):
                title, text = extract_article(url)

            if len(text.strip()) < 300:
                st.error("Not enough article content extracted.")
            else:
                st.subheader("📰 Article Title")
                st.success(title)

                with st.expander("📖 Preview Extracted Content"):
                    st.write(text[:2000])

                # Create dynamic instruction
                if summary_style == "Bullet Points":
                    instruction = f"Summarize in exactly {bullet_count} bullet points."
                elif summary_style == "Paragraph":
                    instruction = f"Provide a {summary_length.lower()} paragraph summary."
                else:
                    instruction = f"Provide a {summary_length.lower()} detailed structured analysis."

                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a professional news analyst."),
                    ("human", f"{instruction}\n\n{{article_text}}")
                ])

                chain = prompt | llm

                with st.spinner("🧠 Generating AI summary..."):
                    response = chain.invoke({"article_text": text})

                st.subheader("📌 AI Summary")
                st.write(response.content)

        except Exception as e:
            st.error("Failed to process article.")
            st.write(str(e))