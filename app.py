import streamlit as st
from openai import OpenAI
import random

client = OpenAI()

# --- ダークモード ---
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.stApp {
    background-color: #0e1117;
}
html, body, [class*="css"] {
    color: white !important;
}
.stButton button {
    background-color: #262730;
    color: white !important;
    border-radius: 8px;
    padding: 8px 16px;
}
.stRadio label {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.title("知財2級AI問題")

# --- 分野 ---
categories = [
    "特許・実用新案","意匠","商標","条約","著作権",
    "不正競争防止法","民法","独占禁止法",
    "種苗法","関税法","外為法","弁理士法"
]

main_category = st.selectbox("分野を選択", categories)

# --- 状態管理 ---
if "problem" not in st.session_state:
    st.session_state.problem = None
    st.session_state.answer = None
    st.session_state.explanation = None
    st.session_state.choices = None
    st.session_state.evidence = None
    st.session_state.answered = False
    st.session_state.problem_type = None

# --- 問題生成 ---
def generate_problem(main):

    trick = random.choice(["あり", "なし"])
    problem_type = random.choice(["適切", "不適切"])

    prompt = f"""
    知的財産管理技能検定2級【学科試験形式】の問題を1問作成してください。

    分野: {main}

    問題形式：
    ・「最も{problem_type}なもの」を選ばせる問題

    条件：
    ・四択問題
    ・実務ではなく知識問題
    ・ひっかけ: {trick}
    ・試験風
    ・簡潔
    ・選択肢はA〜D

    ・必ず「根拠」を付けること
      → 条文番号 or 判例 or 趣旨

    出力形式（厳守）：

    【問題】
    （問題文）

    【選択肢】
    A. ...
    B. ...
    C. ...
    D. ...

    【正解】
    A

    【解説】
    （簡潔）

    【根拠】
    （条文など）
    """

    res = client.chat.completions.create(
        model="gpt-5.4-nano",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content, problem_type


# --- 生成ボタン ---
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

    except:
        st.error("問題の生成に失敗しました。もう一度試してください。")


# --- 問題表示 ---
if st.session_state.problem:

    # --- 問題形式表示（ここが進化ポイント） ---
    if st.session_state.problem_type == "不適切":
        st.markdown("【問題形式】最も <b><u>不適切</u></b> なものを選べ", unsafe_allow_html=True)
    else:
        st.write("【問題形式】最も適切なものを選べ")

    st.write(st.session_state.problem)

    user_choice = st.radio(
        "選択してください",
        st.session_state.choices,
        key="choice"
    )

    # --- 回答 ---
    if st.button("回答する"):

        st.session_state.answered = True

        selected = user_choice[0]

        if selected == st.session_state.answer:
            st.success("正解！⭕")
        else:
            st.error(f"不正解 ❌ 正解は {st.session_state.answer}")

    # --- 回答後のみ表示 ---
    if st.session_state.answered:

        st.write("【解説】")
        st.write(st.session_state.explanation)

        st.write("【根拠】")
        st.info(st.session_state.evidence)
