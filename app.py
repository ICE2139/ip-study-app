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
        "show_category":False,
        "selected_category":None,

        "current":None,
        "answered":False,
        "result":None,

        "wrong_questions":[],

        "practice_stats":defaultdict(lambda: {"total":0,"correct":0}),

        # 模試
        "exam_index":0,
        "exam_answers":[],
        "exam_done":False,
        "exam_start":None,
        "exam_stats":defaultdict(lambda: {"total":0,"correct":0}),
        "current_exam":None,
        "exam_valid_count":0
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
# JSONパース
# =========================
def safe_json(text):
    try:
        return json.loads(text)
    except:
        return None

# =========================
# 問題生成（日本前提は内部のみ）
# =========================
def generate_problem(cat):

    prompt = f"""
あなたは日本の知的財産試験の問題作成者である。

分野:{cat}

【内部前提】
・日本の法律を前提にする（問題文には書かない）
・日本の試験問題として自然にする

【重要制約】
・必ず唯一の正解
・曖昧禁止
・比較・順位禁止
・選択肢は一意に判別可能

【出力形式】
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

            data = safe_json(res.choices[0].message.content)

            if not data:
                continue

            # 選択肢補強
            fixed = []
            for c in data["choices"]:
                if len(c) < 20:
                    c += "（条件あり）"
                fixed.append(c)

            random.shuffle(fixed)

            labels = ["A","B","C","D"]
            data["choices"] = [f"{labels[i]}. {fixed[i]}" for i in range(4)]

            if data["answer"] not in labels:
                continue

            data["cat"] = cat

            return data

        except:
            continue

    return {
        "cat":cat,
        "question":"生成失敗",
        "choices":["A.-","B.-","C.-","D.-"],
        "answer":"A",
        "explanation":"",
        "evidence":""
    }

# =========================
# タイマー（70分）
# =========================
def show_timer():

    if not st.session_state.exam_start:
        return

    elapsed = int(time.time() - st.session_state.exam_start)
    remaining = 70*60 - elapsed

    if remaining <= 0:
        st.error("時間終了")
        return

    m = remaining // 60
    s = remaining % 60

    color = "red" if remaining <= 600 else "white"

    st.markdown(f"""
    <div style="
    position:fixed;
    top:10px;
    right:20px;
    background:#222;
    color:{color};
    padding:10px;
    border-radius:8px;
    font-weight:bold;
    z-index:999;">
    ⏰ {m:02d}:{s:02d}
    </div>
    """, unsafe_allow_html=True)

# =========================
# 回答処理（演習）
# =========================
def submit_answer(choice):

    q = st.session_state.current
    st.session_state.answered = True

    if choice and choice.startswith(q["answer"]):
        st.session_state.result = "correct"
    else:
        st.session_state.result = "wrong"
        st.session_state.wrong_questions.append({"data":q,"mode":"practice"})

    st.session_state.practice_stats[q["cat"]]["total"] += 1

    if st.session_state.result == "correct":
        st.session_state.practice_stats[q["cat"]]["correct"] += 1

# =========================
# 模試
# =========================
def start_exam():

    st.session_state.exam_index = 0
    st.session_state.exam_answers = []
    st.session_state.exam_done = False
    st.session_state.exam_start = time.time()
    st.session_state.exam_stats = defaultdict(lambda: {"total":0,"correct":0})
    st.session_state.exam_valid_count = 0

    st.session_state.current_exam = generate_problem(random.choice(CATEGORIES))

def next_exam(choice):

    q = st.session_state.current_exam

    if not q or q["question"] == "生成失敗":
        st.session_state.current_exam = generate_problem(random.choice(CATEGORIES))
        return

    cat = q["cat"]

    st.session_state.exam_stats[cat]["total"] += 1
    st.session_state.exam_valid_count += 1

    if choice and choice.startswith(q["answer"]):
        st.session_state.exam_stats[cat]["correct"] += 1
    else:
        st.session_state.wrong_questions.append({"data":q,"mode":"exam"})

    st.session_state.exam_answers.append(choice[0])
    st.session_state.exam_index += 1

    if st.session_state.exam_valid_count >= 40:
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

    st.title("知財2級学科AIサイト(ver.1.7.8)")

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

    # 分野表示
    if st.session_state.selected_category:
        st.markdown(f"### 📘 分野：{st.session_state.selected_category}")

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

    show_timer()

    st.button("戻る", on_click=go, args=("menu",))

    if st.session_state.current_exam is None:
        st.button("試験開始", on_click=start_exam)

    elif not st.session_state.exam_done:

        q = st.session_state.current_exam
        i = st.session_state.exam_index

        st.write(f"Q{i+1}/40")

        if q:
            st.write(q["question"])
        else:
            st.write("生成失敗")

        choice = st.radio("", q.get("choices",["A","B","C","D"]), key=i)

        if st.button("次へ"):
            next_exam(choice)

    else:

        total_correct = sum(v["correct"] for v in st.session_state.exam_stats.values())

        st.success(f"{total_correct}/40")

        for cat,v in st.session_state.exam_stats.items():
            if v["total"]:
                st.write(f"{cat}: {v['correct']/v['total']*100:.1f}%")

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

        st.write(f"【復習】{item['mode']}")

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
