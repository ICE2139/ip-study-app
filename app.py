import streamlit as st
from openai import OpenAI
import json, time, random
from collections import defaultdict

client = OpenAI()

# =========================
# 初期化
# =========================
def init():
    defaults = {
        "page":"menu",
        "show_category":False,
        "selected_category":None,
        "current":None,
        "answered":False,
        "result":None,
        "wrong_questions":[],
        "practice_stats":defaultdict(lambda: {"total":0,"correct":0}),
        "exam_index":0,
        "exam_answers":[],
        "exam_done":False,
        "exam_start":None,
        "exam_stats":defaultdict(lambda: {"total":0,"correct":0}),
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# =========================
# 分野（完全版）
# =========================
CATEGORIES = [
    "特許・実用新案","意匠","商標","条約","著作権",
    "不正競争防止法","民法","独占禁止法",
    "種苗法","関税法","外為法","弁理士法"
]

# =========================
# 安全生成（緩和版）
# =========================
def generate_problem(cat):

    prompt = f"""
知財2級 学科

分野:{cat}

・4択
・正解は1つ
・「最も適切」or「__不適切__」
・choicesはシンプルに

JSON:
{{
"question":"",
"choices":["","","",""],
"answer":"A",
"explanation":"",
"evidence":""
}}
"""

    for _ in range(3):

        try:
            res = client.chat.completions.create(
                model="gpt-5.4-nano",
                messages=[{"role":"user","content":prompt}]
            )

            data = json.loads(res.choices[0].message.content)

            if "choices" not in data or len(data["choices"]) != 4:
                continue

            # ラベル付け
            labels = ["A","B","C","D"]
            choices = data["choices"]
            random.shuffle(choices)

            data["choices"] = [f"{labels[i]}. {choices[i]}" for i in range(4)]

            data["cat"] = cat

            return data

        except:
            continue

    # フォールバック
    return {
        "cat":cat,
        "question":"生成失敗（再生成してください）",
        "choices":["A. -","B. -","C. -","D. -"],
        "answer":"A",
        "explanation":"",
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
# 模試（1問ずつ）
# =========================
def start_exam():
    st.session_state.exam_index = 0
    st.session_state.exam_answers = []
    st.session_state.exam_done = False
    st.session_state.exam_start = time.time()
    st.session_state.exam_stats = defaultdict(lambda: {"total":0,"correct":0})

    st.session_state.current_exam = generate_problem(random.choice(CATEGORIES))

def next_exam(choice):

    q = st.session_state.current_exam
    cat = q["cat"]

    st.session_state.exam_stats[cat]["total"] += 1

    if choice.startswith(q["answer"]):
        st.session_state.exam_stats[cat]["correct"] += 1
    else:
        st.session_state.wrong_questions.append(q)

    st.session_state.exam_answers.append(choice[0])
    st.session_state.exam_index += 1

    if st.session_state.exam_index >= 40:
        st.session_state.exam_done = True
    else:
        st.session_state.current_exam = generate_problem(random.choice(CATEGORIES))

# =========================
# ナビ
# =========================
def go(p): st.session_state.page = p
def toggle(): st.session_state.show_category = not st.session_state.show_category
def select(cat):
    st.session_state.selected_category = cat
    st.session_state.show_category = False

# =========================
# UI
# =========================
if st.session_state.page == "menu":

    st.title("知財2級AIサイト(ver.1.7.4)")

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
            st.button(c, on_click=select, args=(c,))

    if st.session_state.selected_category:
        st.write(f"選択中：{st.session_state.selected_category}")

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

    if st.session_state.exam_start is None:
        st.button("試験開始", on_click=start_exam)

    elif not st.session_state.exam_done:

        i = st.session_state.exam_index
        q = st.session_state.current_exam

        st.write(f"Q{i+1}/40")
        st.write(q["question"])

        choice = st.radio("", q["choices"], key=i)

        if st.button("次へ"):
            next_exam(choice)

    else:
        correct = sum(v["correct"] for v in st.session_state.exam_stats.values())
        rate = correct / 40 * 100

        st.success(f"{correct}/40 ({rate:.1f}%)")

        st.write("分野別正答率")
        for cat, v in st.session_state.exam_stats.items():
            if v["total"] > 0:
                r = v["correct"]/v["total"]*100
                st.write(f"{cat}: {r:.1f}%")

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
            st.write(f"正解：{q['answer']}")
