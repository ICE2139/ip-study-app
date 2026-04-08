import streamlit as st
from openai import OpenAI
import json
import time
import random
from collections import defaultdict

client = OpenAI()

# =========================
# 初期化（壊れない版）
# =========================
def init():
    if "page" not in st.session_state:
        st.session_state.page = "menu"

    if "selected_category" not in st.session_state:
        st.session_state.selected_category = None

    if "show_category" not in st.session_state:
        st.session_state.show_category = False

    if "current" not in st.session_state:
        st.session_state.current = None

    if "answered" not in st.session_state:
        st.session_state.answered = False

    if "result" not in st.session_state:
        st.session_state.result = None

    # ★消えないようにする
    if "wrong_questions" not in st.session_state:
        st.session_state.wrong_questions = []

    # 模試
    if "exam_index" not in st.session_state:
        st.session_state.exam_index = 0

    if "exam_done" not in st.session_state:
        st.session_state.exam_done = False

    if "exam_start" not in st.session_state:
        st.session_state.exam_start = None

    if "exam_stats" not in st.session_state:
        st.session_state.exam_stats = defaultdict(lambda: {"total":0,"correct":0})

    if "current_exam" not in st.session_state:
        st.session_state.current_exam = None

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
# 問題生成（完全安定）
# =========================
def generate_problem(cat):

    prompt = f"""
分野：{cat}

知財2級 学科試験レベルの択一問題を作成せよ。

条件：
・必ず正解は1つ
・4択
・条文知識中心
・各選択肢ごとに理由を書く

JSON：
{{
"question":"",
"choices":["","","",""],
"answer":"A",
"choice_explanations":{{
"A":"","B":"","C":"","D":""
}}
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

        new_explain = {}

        for i, (k,v) in enumerate(mapping.items()):
            new_explain[k] = data["choice_explanations"][labels[i]]

        for k,v in mapping.items():
            if v == correct:
                data["answer"] = k

        data["choices"] = [f"{k}. {v}" for k,v in mapping.items()]
        data["choice_explanations"] = new_explain
        data["cat"] = cat

        return data

    except:
        return {
            "cat":cat,
            "question":"生成失敗",
            "choices":["A.-","B.-","C.-","D.-"],
            "answer":"A",
            "choice_explanations":{"A":"-","B":"-","C":"-","D":"-"}
        }

# =========================
# タイマー（軽量）
# =========================
def show_timer():
    if not st.session_state.exam_start:
        return

    elapsed = int(time.time() - st.session_state.exam_start)
    remaining = 70*60 - elapsed

    m = max(0, remaining // 60)
    s = max(0, remaining % 60)

    color = "#ff4b4b" if remaining <= 600 else "#ffffff"

    st.markdown(f"""
    <div style="position:fixed;top:80px;right:20px;
    background:#000;color:{color};
    padding:10px;border-radius:8px;">
    ⏰ {m:02d}:{s:02d}
    </div>
    """, unsafe_allow_html=True)

# =========================
# 回答
# =========================
def submit_answer(choice):

    q = st.session_state.current
    st.session_state.answered = True

    if choice and choice.startswith(q["answer"]):
        st.session_state.result = "correct"
    else:
        st.session_state.result = "wrong"

        # ★確実保存
        st.session_state.wrong_questions.append({
            "data": q,
            "mode": "practice"
        })

# =========================
# 模試
# =========================
def start_exam():
    st.session_state.exam_index = 0
    st.session_state.exam_done = False
    st.session_state.exam_start = time.time()
    st.session_state.exam_stats = defaultdict(lambda: {"total":0,"correct":0})

    st.session_state.current_exam = generate_problem(random.choice(CATEGORIES))

def next_exam(choice):

    q = st.session_state.current_exam

    if q["question"] == "生成失敗":
        st.session_state.current_exam = generate_problem(random.choice(CATEGORIES))
        return

    cat = q["cat"]

    st.session_state.exam_stats[cat]["total"] += 1

    if choice and choice.startswith(q["answer"]):
        st.session_state.exam_stats[cat]["correct"] += 1
    else:
        st.session_state.wrong_questions.append({
            "data": q,
            "mode": "exam"
        })

    st.session_state.exam_index += 1

    if st.session_state.exam_index >= 40:
        st.session_state.exam_done = True
    else:
        st.session_state.current_exam = generate_problem(random.choice(CATEGORIES))

# =========================
# UI操作
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

    st.title("知財2級学科AIサイト(ver.1.7.17)")

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

        st.write(f"### {st.session_state.selected_category}")

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
                st.success(f"正解（{q['answer']}）")
            else:
                st.error(f"不正解（正解：{q['answer']}）")

            st.write("### 各選択肢の解説")
            for k in ["A","B","C","D"]:
                st.write(f"{k}: {q['choice_explanations'][k]}")

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

        st.write(f"【{item['mode']}】")
        st.write(q["question"])

        choice = st.radio("", q["choices"])

        if st.button("回答"):

            if choice and choice.startswith(q["answer"]):
                st.success("正解")
                st.session_state.wrong_questions.pop(0)
                st.rerun()
            else:
                st.error(f"不正解（正解：{q['answer']}）")

                for k in ["A","B","C","D"]:
                    st.write(f"{k}: {q['choice_explanations'][k]}")
