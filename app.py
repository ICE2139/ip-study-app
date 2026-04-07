import streamlit as st
from openai import OpenAI
import random, time, json
from collections import defaultdict

client = OpenAI()

# =========================
# UI
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
    margin-bottom: 15px;
}
.stButton button {
    width: 100%;
    background-color: #262730;
    color: white !important;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 初期化
# =========================
if "page" not in st.session_state:
    st.session_state.page = "menu"

if "practice_stats" not in st.session_state:
    st.session_state.practice_stats = defaultdict(lambda: {"total":0,"correct":0})

if "exam_stats" not in st.session_state:
    st.session_state.exam_stats = defaultdict(lambda: {"total":0,"correct":0})

if "wrong_log" not in st.session_state:
    st.session_state.wrong_log = []

# =========================
# 問題生成（超強化版）
# =========================
def generate_problem(main):

    prompt = f"""
知的財産管理技能検定2級（学科）の問題を作成

分野: {main}

条件：
・四択
・知識問題のみ
・選択肢だけで正誤が判断できること
・正解は必ず1つ
・他の3つは明確に誤り
・曖昧な表現禁止
・選択肢のレベルを揃える
・正解と誤答の違いが明確になるようにする

JSONのみで出力：

{{
 "question": "...",
 "choices": ["A...", "B...", "C...", "D..."],
 "answer": "A",
 "explanation": "...",
 "evidence": "..."
}}
"""

    while True:
        res = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{"role":"user","content":prompt}]
        )

        raw = res.choices[0].message.content

        try:
            data = json.loads(raw)
            if len(data["choices"]) == 4:
                return data
        except:
            continue

# =========================
# メニュー
# =========================
if st.session_state.page == "menu":

    st.title("知財2級AIアプリ(ver.1.6.1)")

    if st.button("問題演習"):
        st.session_state.page = "practice"

    if st.button("模擬試験"):
        st.session_state.page = "exam"

    if st.button("弱点分析"):
        st.session_state.page = "analysis"

    if st.button("復習"):
        st.session_state.page = "review"

# =========================
# 問題演習
# =========================
elif st.session_state.page == "practice":

    if st.button("戻る"):
        st.session_state.page = "menu"

    category = st.selectbox("分野",[
        "特許・実用新案","意匠","商標","条約","著作権",
        "不正競争防止法","民法","独占禁止法",
        "種苗法","関税法","外為法","弁理士法"
    ])

    if st.button("問題生成"):
        st.session_state.current = generate_problem(category)
        st.session_state.current["cat"] = category
        st.session_state.answered = False

    # ★問題生成後のみ表示（グレー枠対策）
    if "current" in st.session_state:

        data = st.session_state.current

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(data["question"])
        st.markdown('</div>', unsafe_allow_html=True)

        # ★choicesがある時だけ表示
        if data["choices"]:
            choice = st.radio("選択", data["choices"], key="practice_choice")

            if st.button("回答"):

                st.session_state.answered = True
                st.session_state.practice_stats[data["cat"]]["total"] += 1

                if choice[0] == data["answer"]:
                    st.success("正解")
                    st.session_state.practice_stats[data["cat"]]["correct"] += 1
                else:
                    st.error("不正解")
                    st.session_state.wrong_log.append(data)

        if st.session_state.get("answered"):
            st.info(data["explanation"])
            st.write("根拠")
            st.write(data["evidence"])

# =========================
# 模擬試験
# =========================
elif st.session_state.page == "exam":

    if st.button("戻る"):
        st.session_state.page = "menu"

    if "exam_started" not in st.session_state:
        st.session_state.exam_started = False

    if not st.session_state.exam_started:

        if st.button("試験開始"):

            st.session_state.exam_started = True
            st.session_state.start_time = time.time()
            st.session_state.exam_data = []
            st.session_state.exam_answers = {}

            dist=(["特許・実用新案"]*12+["商標"]*6+["著作権"]*6+
                  ["意匠"]*4+["条約"]*3+["不正競争防止法"]*3+
                  ["民法","独占禁止法","種苗法","関税法","外為法","弁理士法"])

            random.shuffle(dist)

            for cat in dist:
                d = generate_problem(cat)
                d["category"] = cat
                st.session_state.exam_data.append(d)

    if st.session_state.exam_started:

        remain = int(3600 - (time.time() - st.session_state.start_time))
        st.write(f"残り時間：{remain//60}分")

        for i, q in enumerate(st.session_state.exam_data):
            st.write(f"Q{i+1}")
            st.write(q["question"])
            ch = st.radio("選択", q["choices"], key=f"ex{i}")
            st.session_state.exam_answers[i] = ch[0]

        if st.button("試験終了"):

            stats = defaultdict(lambda: {"total":0,"correct":0})
            score = 0

            for i, q in enumerate(st.session_state.exam_data):
                cat = q["category"]
                stats[cat]["total"] += 1
                st.session_state.exam_stats[cat]["total"] += 1

                if st.session_state.exam_answers.get(i) == q["answer"]:
                    score += 1
                    stats[cat]["correct"] += 1
                    st.session_state.exam_stats[cat]["correct"] += 1

            rate = score / 40 * 100

            st.title("試験結果")
            st.write(f"{score}/40 ({rate:.1f}%)")

            st.write("■ 分野別")
            for cat,data in stats.items():
                r=data["correct"]/data["total"]*100
                st.write(f"{cat}:{data['correct']}/{data['total']} ({r:.1f}%)")

# =========================
# 弱点分析
# =========================
elif st.session_state.page == "analysis":

    if st.button("戻る"):
        st.session_state.page="menu"

    st.write("■ 問題演習")
    for cat,data in st.session_state.practice_stats.items():
        r=data["correct"]/data["total"]*100 if data["total"] else 0
        st.write(f"{cat} ({data['correct']}/{data['total']}) {r:.1f}%")

    st.write("■ 模擬試験")
    for cat,data in st.session_state.exam_stats.items():
        r=data["correct"]/data["total"]*100 if data["total"] else 0
        st.write(f"{cat} ({data['correct']}/{data['total']}) {r:.1f}%")

# =========================
# 復習
# =========================
elif st.session_state.page == "review":

    if st.button("戻る"):
        st.session_state.page="menu"

    if not st.session_state.wrong_log:
        st.write("ミスなし")
    else:
        for w in st.session_state.wrong_log:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write(w["question"])
            st.write("解説")
            st.write(w["explanation"])
            st.markdown('</div>', unsafe_allow_html=True)
