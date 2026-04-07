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
        "page": "menu",
        "show_category": False,
        "selected_category": None,
        "current": None,
        "answered": False,
        "result": None,
        "wrong_questions": [],
        "practice_stats": defaultdict(lambda: {"total":0,"correct":0}),
        "exam_questions": None,
        "exam_index": 0,
        "exam_answers": [],
        "exam_done": False
    }

    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# =========================
# スタイル
# =========================
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}
button {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# ユーティリティ
# =========================
def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        return None

def validate(data):
    if not isinstance(data, dict):
        return False
    keys = ["question","choices","answer","explanation","evidence"]
    for k in keys:
        if k not in data:
            return False
    if len(data["choices"]) != 4:
        return False
    if data["answer"] not in ["A","B","C","D"]:
        return False
    return True

# =========================
# 問題生成（強化版）
# =========================
def generate_problem(cat):

    prompt = f"""
知的財産管理技能検定2級

分野:{cat}

・4択
・1つだけ正解
・選択肢の難易度を揃える
・「最も適切」または「__不適切__」

JSONのみで出力
"""

    for _ in range(3):

        res = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{"role":"user","content":prompt}]
        )

        data = safe_json_parse(res.choices[0].message.content)

        if not data or not validate(data):
            continue

        choices = data["choices"]
        random.shuffle(choices)

        labels = ["A","B","C","D"]

        data["choices"] = [f"{labels[i]}. {choices[i]}" for i in range(4)]

        if data["answer"] not in labels:
            continue

        return data

    return {
        "question":"生成失敗",
        "choices":["A. -","B. -","C. -","D. -"],
        "answer":"A",
        "explanation":"エラー",
        "evidence":""
    }

# =========================
# 回答処理
# =========================
def submit_answer(choice):

    d = st.session_state.current

    st.session_state.answered = True

    if choice and choice.startswith(d["answer"]):
        st.session_state.result = "correct"
    else:
        st.session_state.result = "wrong"
        st.session_state.wrong_questions.append(d)

    st.session_state.practice_stats[d["cat"]]["total"] += 1

    if st.session_state.result == "correct":
        st.session_state.practice_stats[d["cat"]]["correct"] += 1

# =========================
# 模試
# =========================
def start_exam():

    weighted = (
        ["特許・実用新案"] * 10 +
        ["商標"] * 8 +
        ["意匠"] * 6 +
        ["著作権"] * 6 +
        ["条約"] * 4 +
        ["その他"] * 6
    )

    random.shuffle(weighted)

    st.session_state.exam_questions = [
        generate_problem(c) for c in weighted
    ]

    st.session_state.exam_index = 0
    st.session_state.exam_answers = []
    st.session_state.exam_done = False
    st.session_state.exam_start = time.time()

def submit_exam():

    correct = 0
    stats = defaultdict(lambda: {"total":0,"correct":0})

    for q, a in zip(st.session_state.exam_questions, st.session_state.exam_answers):

        stats[q.get("cat","その他")]["total"] += 1

        if a == q["answer"]:
            correct += 1
            stats[q.get("cat","その他")]["correct"] += 1
        else:
            st.session_state.wrong_questions.append(q)

    rate = correct / 40 * 100

    st.session_state.exam_result = {
        "score": correct,
        "rate": rate,
        "stats": stats
    }

    st.session_state.exam_done = True

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

# =========================
# UI
# =========================

if st.session_state.page == "menu":

    st.title("知財2級アプリ(ver.1.7.3)")

    st.button("問題演習", on_click=go, args=("practice",))
    st.button("模擬試験", on_click=go, args=("exam",))
    st.button("復習", on_click=go, args=("review",))

# =========================
# 問題演習
# =========================
elif st.session_state.page == "practice":

    st.button("戻る", on_click=go, args=("menu",))

    st.button("分野選択", on_click=toggle_category)

    if st.session_state.show_category:
        cats = ["特許・実用新案","意匠","商標","条約","著作権"]
        for c in cats:
            st.button(c, on_click=select_category, args=(c,))

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
            submit_answer(choice)

        if st.session_state.answered:

            if st.session_state.result == "correct":
                st.success("正解")
            else:
                st.error(f"不正解（正解：{q['answer']}）")

            st.write(q["explanation"])
            st.write(q["evidence"])

# =========================
# 模試
# =========================
elif st.session_state.page == "exam":

    st.button("戻る", on_click=go, args=("menu",))

    if st.session_state.exam_questions is None:
        st.button("試験開始", on_click=start_exam)

    else:

        if not st.session_state.exam_done:

            i = st.session_state.exam_index
            q = st.session_state.exam_questions[i]

            st.write(f"Q{i+1}/40")
            st.write(q["question"])

            choice = st.radio("", q["choices"], key=i)

            if st.button("次へ"):
                st.session_state.exam_answers.append(choice[0])
                st.session_state.exam_index += 1

                if st.session_state.exam_index >= 40:
                    submit_exam()

        else:

            r = st.session_state.exam_result

            st.success(f"{r['score']}/40")
            st.write(f"{r['rate']}%")

            for cat, v in r["stats"].items():
                rate = v["correct"]/v["total"]*100
                st.write(f"{cat}: {rate:.1f}%")

# =========================
# 復習
# =========================
elif st.session_state.page == "review":

    st.button("戻る", on_click=go, args=("menu",))

    if not st.session_state.wrong_questions:
        st.write("なし")
    else:
        for q in st.session_state.wrong_questions:
            st.write(q["question"])
            for c in q["choices"]:
                st.write(c)
            st.write(q["answer"])
