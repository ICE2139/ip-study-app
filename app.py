import streamlit as st
from openai import OpenAI
import random

client = OpenAI()

# --- 背景反転（ダークモード風） ---
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.stApp {
    background-color: #0e1117;
}
</style>
""", unsafe_allow_html=True)

st.title("知財2級AI問題アプリ")

# --- 大分類 ---
categories = [
    "特許・実用新案",
    "意匠",
    "商標",
    "条約",
    "著作権",
    "不正競争防止法",
    "民法",
    "独占禁止法",
    "種苗法",
    "関税法",
    "外為法",
    "弁理士法"
]

main_category = st.selectbox("分野を選択", categories)

# --- モード ---
mode = st.radio("モード選択", ["ランダム出題", "分野別集中"])

# --- 内部分類 ---
classification = {
    "特許・実用新案": [
        "特許要件", "出願手続", "審査", "権利範囲", "侵害", "ライセンス", "実用新案"
    ],
    "意匠": [
        "登録要件", "出願手続", "権利範囲", "侵害"
    ],
    "商標": [
        "登録要件", "類否判断", "出願手続", "権利範囲", "侵害"
    ],
    "条約": [
        "パリ条約", "PCT", "TRIPS", "ベルヌ条約"
    ],
    "著作権": [
        "著作物", "著作者", "人格権", "財産権", "制限規定", "侵害"
    ],
    "不正競争防止法": [
        "営業秘密", "不正競争行為", "制裁"
    ],
    "民法": [
        "契約", "債務不履行"
    ],
    "独占禁止法": [
        "独占禁止", "ライセンス関係"
    ],
    "種苗法": [
        "登録要件", "育成者権"
    ],
    "関税法": [
        "輸出入規制"
    ],
    "外為法": [
        "輸出規制"
    ],
    "弁理士法": [
        "業務範囲"
    ]
}

# --- 問題生成 ---
def generate_problem(main, mode):
    if mode == "分野別集中":
        sub = random.choice(classification[main])
    else:
        all_subs = sum(classification.values(), [])
        sub = random.choice(all_subs)

    prompt = f"""
    知的財産管理技能検定2級レベルの問題を1問作成してください。

    分野: {main}
    論点: {sub}

    条件：
    ・ひっかけを必ず含める
    ・知財と関連付ける
    ・基本は4択問題
    ・数値（存続期間・費用など）の問題の場合は記述式
    ・記述式の場合は必ず前提条件（年・状況）を書く
    ・実務・試験形式にする

    出力形式：

    【問題】
    （問題文）

    【選択肢】
    A.
    B.
    C.
    D.

    【正解】

    【解説】
    """

    res = client.chat.completions.create(
        model="gpt-5.4-nano",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content

# --- 実行 ---
if st.button("問題を生成"):
    with st.spinner("生成中..."):
        result = generate_problem(main_category, mode)
        st.write(result)
