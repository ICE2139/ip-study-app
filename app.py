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

        # 復習（改良版）
        "wrong_questions":[],

        "practice_stats":defaultdict(lambda: {"total":0,"correct":0}),

        # 模試
        "exam_index":0,
        "exam_answers":[],
        "exam_done":False,
        "exam_start":None,
        "exam_stats":defaultdict(lambda: {"total":0,"correct":0}),
        "current_exam":None
    }

    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# =========================
# 分野（維持）
# =========================
CATEGORIES = [
    "特許・実用新案","意匠","商標","条約","著作権",
    "不正競争防止法","民法","独占禁止法",
    "種苗法","関税法","外為法","弁理士法"
]

# =========================
# JSON安全
# =========================
def safe_json(text):
    try:
        return json.loads(text)
    except:
        return None

# =========================
# 問題生成（強化）
# =========================
def generate_problem(cat):

    prompt = f"""
知財2級 学科

分野:{cat}

必須：
・4択
・1つだけ正解
・選択肢は具体的で区別可能にする
・抽象的禁止（正しい・誤りだけは禁止）
・「最も適切」または「__不適切__」

JSON形式：
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

            if not data or "choices" not in data:
                continue

            if len(data["choices"]) != 4:
                continue

            # 具体性補強
            enhanced = []
            for c in data["choices"]:
                if len(c) < 12:
                    c += "（具体的条件付き）"
                enhanced.append(c)

            random.shuffle(enhanced)

            labels = ["A","B","C","D"]
            data["choices"] = [f"{labels[i]}. {enhanced[i]}" for i in range(4)]

            data["cat"] = cat

            if data["answer"] not in labels:
                continue

            return data

        except:
            continue

    return {
        "cat":cat,
        "question":"生成失敗",
        "choices":["A. -","B. -","C. -","D. -"],
        "answer":"A",
        "explanation":"",
        "evidence":""
    }

# =========================
# 回答処理（問題演習）
# =========================
def submit_answer(choice):

    d = st.session_state.current
    st.session_state.answered = True

    if choice and choice.startswith(d["answer"]):
        st.session_state.result = "correct"
    else:
        st.session_state.result = "wrong"

        # ★復習用に保存（モード付き）
        st.session_state.wrong_questions.append({
            "data": d,
            "mode": "practice"
        })

    st.session_state.practice_stats[d["cat"]]["total"] += 1

    if st.session_state.result == "correct":
        st.session_state.practice_stats[d["cat"]]["correct"] += 1

# =========================
# 模試
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
    cat = q.get("cat","その他")

    st.session_state.exam_stats[cat]["total"] += 1

    if choice and choice.startswith(q["answer"]):
        st.session_state.exam_stats[cat]["correct"] += 1
    else:
        st.session_state.wrong_questions.append({
            "data": q,
            "mode": "exam"
        })

    st.session_state.exam_answers.append(choice[0] if choice else "A")

    st.session_state.exam_index += 1

    if st.session_state.exam_index < 40:
        st.session_state.current_exam = generate_problem(random.choice(CATEGORIES))
    else:
        st.session_state.exam_done = True

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

    st.title("知財2級AIサイト(ver.1.7.5)")

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

    if st.session_state.current_exam is None:
        st.button("試験開始", on_click=start_exam)

    elif not st.session_state.exam_done:

        i = st.session_state.exam_index
        q = st.session_state.current_exam

        st.write(f"Q{i+1}/40")

        if not q:
            st.write("生成失敗")
        else:
            st.write(q["question"])

        choice = st.radio("", q.get("choices",["A","B","C","D"]), key=i)

        if st.button("次へ"):
            next_exam(choice)

    else:

        total_correct = sum(v["correct"] for v in st.session_state.exam_stats.values())
        rate = total_correct / 40 * 100

        st.success(f"{total_correct}/40 ({rate:.1f}%)")

        st.write("分野別正答率")

        for cat, v in st.session_state.exam_stats.items():
            if v["total"] > 0:
                r = v["correct"]/v["total"]*100
                st.write(f"{cat}: {r:.1f}%")

# =========================
# 復習（完全版）
# =========================
elif st.session_state.page == "review":

    st.button("戻る", on_click=go, args=("menu",))

    if not st.session_state.wrong_questions:
        st.write("間違えた問題はありません")
    else:

        item = st.session_state.wrong_questions[0]
        q = item["data"]
        mode = item["mode"]

        st.write(f"【復習】（{mode}）")

        st.write(q["question"])

        choice = st.radio("", q["choices"], key="review")

        if st.button("回答（復習）"):

            if choice and choice.startswith(q["answer"]):
                st.success("正解")

                # 正解なら削除
                st.session_state.wrong_questions.pop(0)

                st.rerun()

            else:
                st.error(f"不正解（正解：{q['answer']}）")
                st.write(q["explanation"])
                st.write(q["evidence"])

        if st.button("次の問題"):
            st.session_state.wrong_questions.append(
                st.session_state.wrong_questions.pop(0)
            )
            st.rerun()
