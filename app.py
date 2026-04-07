import streamlit as st
from openai import OpenAI
import json
import time
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

    if "wrong_questions" not in st.session_state:
        st.session_state.wrong_questions = []

    if "practice_stats" not in st.session_state:
        st.session_state.practice_stats = defaultdict(lambda: {"total":0,"correct":0})

init()

# =========================
# UIスタイル
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
# 回答処理（演習）
# =========================
def submit_answer(choice):
    d = st.session_state.current

    st.session_state.answered = True
    st.session_state.practice_stats[d["cat"]]["total"] += 1

    if choice[0] == d["answer"]:
        st.session_state.practice_stats[d["cat"]]["correct"] += 1
        st.session_state.result = "correct"
    else:
        st.session_state.result = "wrong"
        st.session_state.wrong_questions.append(d)

# =========================
# 模試開始
# =========================
def start_exam():

    categories = (
        ["特許・実用新案"] * 10 +
        ["商標"] * 8 +
        ["意匠"] * 6 +
        ["著作権"] * 6 +
        ["条約"] * 4 +
        ["その他"] * 6
    )

    st.session_state.exam_questions = [generate_problem(c) for c in categories]

    st.session_state.exam_index = 0
    st.session_state.exam_answers = []
    st.session_state.exam_start = time.time()
    st.session_state.exam_done = False

# =========================
# 模試採点
# =========================
def submit_exam():

    correct = 0

    for q, a in zip(st.session_state.exam_questions, st.session_state.exam_answers):
        if a == q["answer"]:
            correct += 1
        else:
            st.session_state.wrong_questions.append(q)

    rate = correct / 40 * 100

    st.session_state.exam_result = {
        "score": correct,
        "rate": rate,
        "pass": rate >= 80
    }

    st.session_state.exam_done = True

# =========================
# メニュー
# =========================
if st.session_state.page == "menu":

    st.title("知財2級AIアプリ(ver.1.7.0)")

    st.button("問題演習", on_click=go, args=("practice",))
    st.button("模擬試験", on_click=go, args=("exam",))
    st.button("復習", on_click=go, args=("review",))

# =========================
# 問題演習
# =========================
elif st.session_state.page == "practice":

    st.button("戻る", on_click=go, args=("menu",))

    st.button("分野を選択 ▼", on_click=toggle_category)

    if st.session_state.show_category:
        categories = [
            "特許・実用新案","意匠","商標","条約","著作権",
            "不正競争防止法","民法","独占禁止法",
            "種苗法","関税法","外為法","弁理士法"
        ]
        for c in categories:
            st.button(c, on_click=select_category, args=(c,))

    if st.session_state.selected_category:
        st.write(f"選択中：{st.session_state.selected_category}")
        st.button("問題生成", on_click=lambda: st.session_state.update({
            "current": generate_problem(st.session_state.selected_category),
            "answered": False
        }))

    if st.session_state.current:

        d = st.session_state.current

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(d["question"])
        st.markdown('</div>', unsafe_allow_html=True)

        choice = st.radio("", d["choices"])

        st.button("回答", on_click=submit_answer, args=(choice,))

        if st.session_state.answered:

            if st.session_state.result == "correct":
                st.success("正解！")
            else:
                st.error(f"不正解（正解：{d['answer']}）")

            st.info(d["explanation"])
            st.write(d["evidence"])

# =========================
# 模試
# =========================
elif st.session_state.page == "exam":

    st.button("戻る", on_click=go, args=("menu",))

    if "exam_questions" not in st.session_state:
        st.button("試験開始", on_click=start_exam)

    if "exam_questions" in st.session_state:

        elapsed = time.time() - st.session_state.exam_start
        remaining = 3600 - elapsed

        st.write(f"残り時間：{int(remaining//60)}分")

        if remaining <= 0 and not st.session_state.exam_done:
            submit_exam()

        if not st.session_state.exam_done:

            i = st.session_state.exam_index
            q = st.session_state.exam_questions[i]

            st.write(f"Q{i+1}/40")
            st.write(q["question"])

            choice = st.radio("", q["choices"], key=i)

            if st.button("回答して次へ"):
                st.session_state.exam_answers.append(choice[0])
                st.session_state.exam_index += 1

                if st.session_state.exam_index >= 40:
                    submit_exam()

        else:
            r = st.session_state.exam_result

            st.success(f"得点：{r['score']}/40")
            st.write(f"正答率：{r['rate']}%")

            if r["pass"]:
                st.success("合格！")
            else:
                st.error("不合格")

# =========================
# 復習
# =========================
elif st.session_state.page == "review":

    st.button("戻る", on_click=go, args=("menu",))

    st.title("復習（間違えた問題）")

    if not st.session_state.wrong_questions:
        st.write("まだ間違いはありません")
    else:
        for q in st.session_state.wrong_questions:

            st.markdown("---")
            st.write(f"【{q['cat']}】{q['question']}")

            for c in q["choices"]:
                st.write(c)

            st.write(f"正解：{q['answer']}")
            st.write(q["explanation"])
