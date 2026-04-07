import streamlit as st
from openai import OpenAI
import random

client = OpenAI()

# --- ダークモード ---
st.markdown("""
<style>
body { background-color: #0e1117; color: white; }
.stApp { background-color: #0e1117; }
html, body, [class*="css"] { color: white !important; }
.stButton button {
    background-color: #262730;
    color: white !important;
    border-radius: 8px;
    padding: 8px 16px;
}
.stRadio label { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 初期状態 ---
if "page" not in st.session_state:
    st.session_state.page = "menu"

if "wrong_questions" not in st.session_state:
    st.session_state.wrong_questions = []

# =========================
# メニュー画面
# =========================
if st.session_state.page == "menu":

    st.title("知財2級AI学習アプリ(ver.1.4.0)")

    if st.button("問題演習"):
        st.session_state.page = "practice"

    if st.button("弱点分析"):
        st.session_state.page = "analysis"

    if st.button("間違えた問題復習"):
        st.session_state.page = "review"


# =========================
# 問題演習画面
# =========================
elif st.session_state.page == "practice":

    st.title("問題演習")

    if st.button("メニューに戻る"):
        st.session_state.page = "menu"

    categories = [
        "特許・実用新案","意匠","商標","条約","著作権",
        "不正競争防止法","民法","独占禁止法",
        "種苗法","関税法","外為法","弁理士法"
    ]

    main_category = st.selectbox("分野を選択", categories)

    if "problem" not in st.session_state:
        st.session_state.problem = None

    def generate_problem(main):

        trick = random.choice(["あり", "なし"])
        problem_type = random.choice(["適切", "不適切"])
        past_exam = random.choice(["含める", "含めない"])

        prompt = f"""
知財2級の学科問題を作成

分野: {main}

問題形式：
・最も{problem_type}なもの

条件：
・不適切問題 → 正しい3つ＋誤り1つ（自然に紛らわしく）
・適切問題 → 正解1つ＋誤り3つ

・過去問要素: {past_exam}
→ 含める場合は最後に「（第○○回学科より）」と書く

・根拠を必ず書く（条文など）

形式：

【問題】
...

【選択肢】
A...
B...
C...
D...

【正解】
A

【解説】
...

【根拠】
...
"""

        res = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content, problem_type

    if st.button("問題生成"):

        raw, problem_type = generate_problem(main_category)

        try:
            question = raw.split("【選択肢】")[0]
            choices_part = raw.split("【選択肢】")[1].split("【正解】")[0]
            answer = raw.split("【正解】")[1].split("【解説】")[0].strip()
            explanation = raw.split("【解説】")[1].split("【根拠】")[0]
            evidence = raw.split("【根拠】")[1]

            choices = [c.strip() for c in choices_part.split("\n") if c.strip()]

            st.session_state.problem = question
            st.session_state.choices = choices
            st.session_state.answer = answer
            st.session_state.explanation = explanation
            st.session_state.evidence = evidence
            st.session_state.problem_type = problem_type
            st.session_state.answered = False
            st.session_state.category = main_category

        except:
            st.error("生成失敗")

    if st.session_state.problem:

        if st.session_state.problem_type == "不適切":
            st.markdown("最も <u>不適切</u> なものを選べ", unsafe_allow_html=True)
        else:
            st.write("最も適切なものを選べ")

        st.write(st.session_state.problem)

        user_choice = st.radio("選択", st.session_state.choices)

        if st.button("回答する"):

            st.session_state.answered = True
            selected = user_choice[0]

            if selected == st.session_state.answer:
                st.success("正解")
            else:
                st.error("不正解")

                # --- 間違えた問題保存 ---
                st.session_state.wrong_questions.append({
                    "question": st.session_state.problem,
                    "category": st.session_state.category
                })

        if st.session_state.answered:
            st.write("【解説】")
            st.write(st.session_state.explanation)
            st.write("【根拠】")
            st.write(st.session_state.evidence)


# =========================
# 復習画面
# =========================
elif st.session_state.page == "review":

    st.title("復習")

    if st.button("メニューに戻る"):
        st.session_state.page = "menu"

    if not st.session_state.wrong_questions:
        st.write("間違えた問題なし")
    else:
        for q in st.session_state.wrong_questions:
            st.write(f"【{q['category']}】")
            st.write(q["question"])
            st.write("---")


# =========================
# AI分析
# =========================
elif st.session_state.page == "analysis":

    st.title("弱点分析")

    if st.button("メニューに戻る"):
        st.session_state.page = "menu"

    if not st.session_state.wrong_questions:
        st.write("データ不足")
    else:

        text = "\n".join([q["category"] for q in st.session_state.wrong_questions])

        prompt = f"""
以下はユーザーが間違えた分野です：

{text}

弱点分野を分析し、
・苦手分野
・改善アドバイス
を簡潔に出してください
"""

        res = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{"role": "user", "content": prompt}]
        )

        st.write(res.choices[0].message.content)
