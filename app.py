import streamlit as st
from openai import OpenAI
import json
from collections import defaultdict

client = OpenAI()

# =========================
# 初期化
# =========================
def init():
    if "page" not in st.session_state:
        st.session_state.page = "menu"

    if "show_category" not in st.session_state:
        st.session_state.show_category = False

    if "selected_category" not in st.session_state:
        st.session_state.selected_category = None

    if "current" not in st.session_state:
        st.session_state.current = None

    if "answered" not in st.session_state:
        st.session_state.answered = False

    if "result" not in st.session_state:
        st.session_state.result = None

    if "practice_stats" not in st.session_state:
        st.session_state.practice_stats = defaultdict(lambda: {"total":0,"correct":0})

init()

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
}
.stButton button {
    width: 100%;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# ナビ
# =========================
def go(page):
    st.session_state.page = page

def toggle_category():
    st.session_state.show_category = not st.session_state.show_category

def select_category(cat):
    st.session_state.selected_category = cat
    st.session_state.show_category = False

def create_problem():
    st.session_state.current = generate_problem(st.session_state.selected_category)
    st.session_state.current["cat"] = st.session_state.selected_category
    st.session_state.answered = False

def submit_answer(choice):
    d = st.session_state.current

    st.session_state.answered = True
    st.session_state.practice_stats[d["cat"]]["total"] += 1

    if choice[0] == d["answer"]:
        st.session_state.practice_stats[d["cat"]]["correct"] += 1
        st.session_state.result = "correct"
    else:
        st.session_state.result = "wrong"

# =========================
# 問題生成
# =========================
def generate_problem(cat):

    prompt = f"""
知的財産管理技能検定2級（学科）

分野:{cat}

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
# メニュー
# =========================
if st.session_state.page == "menu":

    st.title("知財2級AIアプリ(ver.1.6.4)")

    st.button("問題演習", on_click=go, args=("practice",))
    st.button("模擬試験", on_click=go, args=("exam",))
    st.button("弱点分析", on_click=go, args=("analysis",))
    st.button("復習", on_click=go, args=("review",))

# =========================
# 問題演習
# =========================
elif st.session_state.page == "practice":

    st.button("戻る", on_click=go, args=("menu",))

    # ▼ 分野トグル（1クリックで開閉）
    st.button("分野を選択 ▼", on_click=toggle_category)

    if st.session_state.show_category:

        categories = [
            "特許・実用新案","意匠","商標","条約","著作権",
            "不正競争防止法","民法","独占禁止法",
            "種苗法","関税法","外為法","弁理士法"
        ]

        for cat in categories:
            st.button(cat, on_click=select_category, args=(cat,))

    # ▼ 選択中表示
    if st.session_state.selected_category:
        st.write(f"選択中：{st.session_state.selected_category}")
        st.button("問題生成", on_click=create_problem)

    # ▼ 問題表示
    if st.session_state.current:

        d = st.session_state.current

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(d["question"])
        st.markdown('</div>', unsafe_allow_html=True)

        choice = st.radio("", d["choices"])

        st.button("回答", on_click=submit_answer, args=(choice,))

        # ▼ 結果表示（記号のみ）
        if st.session_state.answered:

            if st.session_state.result == "correct":
                st.success("正解！")
            else:
                st.error(f"不正解（正解：{d['answer']}）")

            st.info(d["explanation"])

            st.write("根拠")
            st.write(d["evidence"])
