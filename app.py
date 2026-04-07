import streamlit as st
from openai import OpenAI
import random, time, json
from collections import defaultdict

client = OpenAI()

# =========================
# UI
# =========================
st.markdown("""
<style>
html, body, .stApp {
    background-color: #0e1117 !important;
    color: white !important;
}
.card {
    background-color: #1c1f26;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 15px;
}
.stButton button {
    width: 100%;
    background-color: #262730;
    color: white !important;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 初期化
# =========================
if "page" not in st.session_state:
    st.session_state.page = "menu"

if "show_category" not in st.session_state:
    st.session_state.show_category = False

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

if "practice_stats" not in st.session_state:
    st.session_state.practice_stats = defaultdict(lambda: {"total":0,"correct":0})

if "exam_stats" not in st.session_state:
    st.session_state.exam_stats = defaultdict(lambda: {"total":0,"correct":0})

if "wrong_log" not in st.session_state:
    st.session_state.wrong_log = []

# =========================
# 問題生成
# =========================
def generate_problem(main):

    prompt = f"""
知的財産管理技能検定2級（学科）

分野:{main}

条件：
・四択
・正解1つ
・曖昧禁止
・選択肢だけで判断可能

JSON：
{{
 "question":"...",
 "choices":["A...","B...","C...","D..."],
 "answer":"A",
 "explanation":"...",
 "evidence":"..."
}}
"""

    while True:
        res = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{"role":"user","content":prompt}]
        )
        try:
            data = json.loads(res.choices[0].message.content)
            if len(data["choices"]) == 4:
                return data
        except:
            continue

# =========================
# ページ遷移
# =========================
def go(p):
    st.session_state.page = p

# =========================
# メニュー
# =========================
if st.session_state.page == "menu":

    st.title("知財2級AIアプリ(ver.1.6.2)")

    st.button("問題演習", on_click=go, args=("practice",))
    st.button("模擬試験", on_click=go, args=("exam",))
    st.button("弱点分析", on_click=go, args=("analysis",))
    st.button("復習", on_click=go, args=("review",))

# =========================
# 問題演習
# =========================
elif st.session_state.page == "practice":

    st.button("戻る", on_click=go, args=("menu",))

    # ▼ トグルボタン
    if st.button("分野を選択 ▼"):
        st.session_state.show_category = not st.session_state.show_category

    # ▼ 展開
    if st.session_state.show_category:

        categories = [
            "特許・実用新案","意匠","商標","条約","著作権",
            "不正競争防止法","民法","独占禁止法",
            "種苗法","関税法","外為法","弁理士法"
        ]

        for cat in categories:
            if st.button(cat):
                st.session_state.selected_category = cat
                st.session_state.show_category = False

    if st.session_state.selected_category:
        st.write(f"選択中：{st.session_state.selected_category}")

        if st.button("問題生成"):

            st.session_state.current = generate_problem(st.session_state.selected_category)
            st.session_state.current["cat"] = st.session_state.selected_category
            st.session_state.answered = False

    if "current" in st.session_state:

        d = st.session_state.current

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(d["question"])
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("選択肢")
        choice = st.radio("", d["choices"], key="practice_choice")

        if st.button("回答"):

            st.session_state.answered = True
            st.session_state.practice_stats[d["cat"]]["total"] += 1

            if choice[0] == d["answer"]:
                st.success("正解")
                st.session_state.practice_stats[d["cat"]]["correct"] += 1
            else:
                st.error("不正解")
                st.session_state.wrong_log.append(d)

        if st.session_state.get("answered"):
            st.info(d["explanation"])
            st.write("根拠")
            st.write(d["evidence"])
