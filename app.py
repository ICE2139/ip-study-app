import streamlit as st
from openai import OpenAI
import json
import time
import random
from collections import defaultdict

client = OpenAI()

# =========================
# 初期化
# =========================
def init():
    defaults = {
        "page":"menu",
        "selected_category":None,
        "show_category":False,

        "current":None,
        "answered":False,
        "result":None,

        "wrong_questions":[],

        # 模試
        "exam_questions":[],
        "exam_index":0,
        "exam_done":False,
        "exam_start":None,
        "exam_stats":defaultdict(lambda: {"total":0,"correct":0})
    }

    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# =========================
# 分野
# =========================
CATEGORIES = [
    "特許・実用新案","意匠","商標","条約",
    "著作権","不正競争防止法","民法",
    "独占禁止法","種苗法","関税法","外為法","弁理士法"
]

# =========================
# 問題生成
# =========================
def generate_problem(cat):

    prompt = f"""
分野：{cat}

択一問題を1問作成。
必ず正解は1つ。

JSON:
{{
"question":"",
"choices":["","","",""],
"answer":"A",
"explanation":"",
"evidence":""
}}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{"role":"user","content":prompt}],
            response_format={"type":"json_object"}
        )

        data = json.loads(res.choices[0].message.content)

        correct = data["choices"][0]

        labels = ["A","B","C","D"]
        random.shuffle(data["choices"])

        mapping = dict(zip(labels, data["choices"]))

        for k,v in mapping.items():
            if v == correct:
                data["answer"] = k

        data["choices"] = [f"{k}. {v}" for k,v in mapping.items()]
        data["cat"] = cat

        return data

    except:
        return {
            "cat":cat,
            "question":"生成失敗",
            "choices":["A.-","B.-","C.-","D.-"],
            "answer":"A",
            "explanation":"失敗",
            "evidence":""
        }

# =========================
# タイマー（表示のみ）
# =========================
def show_timer():

    if not st.session_state.exam_start:
        return

    elapsed = int(time.time() - st.session_state.exam_start)
    remaining = 70*60 - elapsed

    if remaining <= 0:
        st.error("試験終了")
        return

    m = remaining // 60
    s = remaining % 60

    color = "#ff4b4b" if remaining <= 600 else "#ffffff"

    st.markdown(f"""
    <div style="
    position:fixed;
    top:80px;
    right:20px;
    background:#000;
    color:{color};
    padding:10px 14px;
    border-radius:8px;
    font-size:18px;
    font-weight:bold;
    border:1px solid {color};
    z-index:9999;
    ">
    ⏰ {m:02d}:{s:02d}
    </div>
    """, unsafe_allow_html=True)

# =========================
# 模試（事前生成）
# =========================
def start_exam():

    st.session_state.exam_questions = []

    for _ in range(40):
        q = generate_problem(random.choice(CATEGORIES))
        st.session_state.exam_questions.append(q)

    st.session_state.exam_index = 0
    st.session_state.exam_done = False
    st.session_state.exam_start = time.time()
    st.session_state.exam_stats = defaultdict(lambda: {"total":0,"correct":0})

def next_exam(choice):

    q = st.session_state.exam_questions[st.session_state.exam_index]

    cat = q["cat"]

    st.session_state.exam_stats[cat]["total"] += 1

    if choice and choice.startswith(q["answer"]):
        st.session_state.exam_stats[cat]["correct"] += 1
    else:
        st.session_state.wrong_questions.append({"data":q,"mode":"exam"})

    st.session_state.exam_index += 1

    if st.session_state.exam_index >= len(st.session_state.exam_questions):
        st.session_state.exam_done = True

# =========================
# UI
# =========================
def go(p): st.session_state.page = p

def toggle():
    st.session_state.show_category = not st.session_state.show_category

def select(cat):
    st.session_state.selected_category = cat
    st.session_state.show_category = False

# =========================
# メニュー
# =========================
if st.session_state.page == "menu":

    st.title("知財2級学科AIサイト(ver.1.7.16)")

    st.button("問題演習", on_click=go, args=("practice",))
    st.button("模擬試験", on_click=go, args=("exam",))
    st.button("復習", on_click=go, args=("review",))

# =========================
# 問題演習
# =========================
elif st.session_state.page == "practice":

    st.button("戻る", on_click=go, args=("menu",))

    st.button("分野選択", on_click=toggle)

    if st.session_state.show_category:
        for c in CATEGORIES:
            if st.button(c):
                select(c)

    if st.session_state.selected_category:

        st.write(st.session_state.selected_category)

        if st.button("問題生成"):
            st.session_state.current = generate_problem(st.session_state.selected_category)
            st.session_state.answered = False

    if st.session_state.current:

        q = st.session_state.current

        st.write(q["question"])

        choice = st.radio("", q["choices"])

        if st.button("回答"):
            st.session_state.answered = True

            if choice and choice.startswith(q["answer"]):
                st.success(f"正解（{q['answer']}）")
            else:
                st.error(f"不正解（正解：{q['answer']}）")

            st.write(q["explanation"])
            st.write(q["evidence"])

# =========================
# 模試
# =========================
elif st.session_state.page == "exam":

    show_timer()

    st.button("戻る", on_click=go, args=("menu",))

    if not st.session_state.exam_questions:
        st.button("試験開始", on_click=start_exam)

    elif not st.session_state.exam_done:

        q = st.session_state.exam_questions[st.session_state.exam_index]

        st.write(f"Q{st.session_state.exam_index+1}/40")

        st.write(q["question"])

        choice = st.radio("", q["choices"], key=st.session_state.exam_index)

        if st.button("次へ"):

            next_exam(choice)

            st.rerun()

    else:

        total = sum(v["correct"] for v in st.session_state.exam_stats.values())

        st.success(f"{total}/40")

# =========================
# 復習
# =========================
elif st.session_state.page == "review":

    st.button("戻る", on_click=go, args=("menu",))

    if not st.session_state.wrong_questions:
        st.write("なし")

    else:
        item = st.session_state.wrong_questions[0]
        q = item["data"]

        st.write(q["question"])

        choice = st.radio("", q["choices"])

        if st.button("回答"):

            if choice and choice.startswith(q["answer"]):
                st.success("正解")
                st.session_state.wrong_questions.pop(0)
                st.rerun()
            else:
                st.error(f"不正解（正解：{q['answer']}）")
                st.write(q["explanation"])
                st.write(q["evidence"])
