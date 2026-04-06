import streamlit as st
import openai
import random

st.set_page_config(layout="wide")

# パスワード
PASSWORD = "1234"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("パスワード", type="password")
    if pwd == PASSWORD:
        st.session_state.auth = True
    else:
        st.stop()

openai.api_key = st.secrets["OPENAI_API_KEY"]

# 分野データ（例：あとで全部入れる）
fields = {
    "特許法・実用新案法": {
        "特許法の目的と保護対象": [
            "特許法はなぜ存在するか",
            "企業経営と特許権の関係",
            "特許出願による経営上の利益",
            "特許と営業秘密の関係",
            "特許法の保護対象である発明とは"
        ]
    }
}

# UI
st.title("知財2級 AI問題アプリ")

main = st.selectbox("大分類", list(fields.keys()))
sub = st.selectbox("小分類", list(fields[main].keys()))

# ミニ分類ランダム
mini = random.choice(fields[main][sub])

# 問題生成
def generate_problem(main, sub, mini):
    prompt = f"""
    知的財産管理技能検定2級（学科）レベルの問題を作成せよ。

    分野: {main} / {sub} / {mini}

    条件:
    ・四択問題
    ・ひっかけを含める
    ・条文理解を問う
    ・基礎〜応用レベル
    ・知的財産と関連付ける
    ・解説は簡潔に
    ・根拠（条文の趣旨）を書く
    ・具体例も書く

    出力形式:
    【問題】
    【選択肢】
    ①
    ②
    ③
    ④
    【正解】
    【解説】
    【根拠】
    【具体例】
    """

    res = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content

# 実行ボタン
if st.button("問題生成"):
    result = generate_problem(main, sub, mini)
    st.write(result)
