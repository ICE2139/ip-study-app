import streamlit as st
from openai import OpenAI

client = OpenAI()

st.title("知財2級AI問題アプリ")

# --- 大分類 ---
main_category = st.selectbox(
    "大分類",
    ["特許", "商標", "意匠", "著作権"]
)

# --- 小分類（大分類に応じて変わる） ---
if main_category == "特許":
    sub_category = st.selectbox(
        "小分類",
        ["新規性", "進歩性", "先願主義", "特許要件"]
    )
elif main_category == "商標":
    sub_category = st.selectbox(
        "小分類",
        ["識別力", "類似", "商標登録要件"]
    )
elif main_category == "意匠":
    sub_category = st.selectbox(
        "小分類",
        ["創作性", "類似意匠", "意匠登録要件"]
    )
else:  # 著作権
    sub_category = st.selectbox(
        "小分類",
        ["著作物性", "権利内容", "保護期間"]
    )

# --- 細分類（難易度） ---
mini_category = st.selectbox(
    "難易度",
    ["初級", "中級", "上級"]
)

# --- 問題生成 ---
def generate_problem(main, sub, mini):
    prompt = f"""
    以下の条件で知的財産管理技能検定2級の問題を1問作ってください。

    大分類: {main}
    小分類: {sub}
    難易度: {mini}

    選択式問題にしてください。
    必ず解説もつけてください。
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return res.choices[0].message.content

# --- 実行ボタン ---
if st.button("問題を生成"):
    with st.spinner("問題生成中..."):
        result = generate_problem(main_category, sub_category, mini_category)
        st.write(result)
