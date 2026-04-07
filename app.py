import streamlit as st
from openai import OpenAI
import random, time
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
    padding: 12px;
}
.stRadio > div {
    background-color: #1c1f26;
    padding: 10px;
    border-radius: 8px;
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
# 問題生成
# =========================
def generate_problem(main):

    problem_type = random.choice(["適切","不適切"])

    prompt = f"""
知的財産管理技能検定2級【学科】問題

分野:{main}

・知識問題のみ
・四択

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
        messages=[{"role":"user","content":prompt}]
    )

    return res.choices[0].message.content, problem_type

# =========================
# メニュー
# =========================
if st.session_state.page == "menu":

    st.title("知財2級AIアプリ(ver.1.5.5)")

    if st.button("問題演習"):
        st.session_state.page = "practice"

    if st.button("模擬試験"):
        st.session_state.page = "exam"

    if st.button("弱点分析"):
        st.session_state.page = "analysis"

    if st.button("復習"):
        st.session_state.page = "review"

# =========================
# 問題演習（修正版）
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

        raw,_ = generate_problem(category)

        q = raw.split("【選択肢】")[0]
        c = raw.split("【選択肢】")[1].split("【正解】")[0]
        a = raw.split("【正解】")[1].split("【解説】")[0].strip()
        ex = raw.split("【解説】")[1].split("【根拠】")[0]
        ev = raw.split("【根拠】")[1]

        st.session_state.current = {
            "q":q,
            "c":[x for x in c.split("\n") if x],
            "a":a,
            "ex":ex,
            "ev":ev,
            "cat":category
        }
        st.session_state.answered=False

    if "current" in st.session_state:

        data = st.session_state.current

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(data["q"])
        st.markdown('</div>', unsafe_allow_html=True)

        choice = st.radio("選択",data["c"])

        if st.button("回答"):

            st.session_state.answered=True
            st.session_state.practice_stats[data["cat"]]["total"] += 1

            if choice[0]==data["a"]:
                st.success("正解")
                st.session_state.practice_stats[data["cat"]]["correct"] += 1
            else:
                st.error("不正解")
                st.session_state.wrong_log.append(data)

        if st.session_state.answered:
            st.info(data["ex"])
            st.write("根拠")
            st.write(data["ev"])

# =========================
# 模擬試験（省略せず完全）
# =========================
elif st.session_state.page == "exam":

    if st.button("戻る"):
        st.session_state.page = "menu"

    if "exam_started" not in st.session_state:
        st.session_state.exam_started=False

    if not st.session_state.exam_started:

        if st.button("試験開始"):

            st.session_state.exam_started=True
            st.session_state.start_time=time.time()
            st.session_state.exam_data=[]
            st.session_state.exam_answers={}

            dist=(["特許・実用新案"]*12+["商標"]*6+["著作権"]*6+
                  ["意匠"]*4+["条約"]*3+["不正競争防止法"]*3+
                  ["民法","独占禁止法","種苗法","関税法","外為法","弁理士法"])

            random.shuffle(dist)

            for cat in dist:
                raw,_=generate_problem(cat)
                q=raw.split("【選択肢】")[0]
                c=raw.split("【選択肢】")[1].split("【正解】")[0]
                a=raw.split("【正解】")[1].split("【解説】")[0].strip()

                st.session_state.exam_data.append({
                    "q":q,
                    "c":[x for x in c.split("\n") if x],
                    "a":a,
                    "category":cat
                })

    if st.session_state.exam_started:

        remain=int(3600-(time.time()-st.session_state.start_time))
        st.write(f"残り時間：{remain//60}分")

        for i,q in enumerate(st.session_state.exam_data):
            st.write(f"Q{i+1}")
            st.write(q["q"])
            ch=st.radio("選択",q["c"],key=f"ex{i}")
            st.session_state.exam_answers[i]=ch[0]

        if st.button("試験終了"):

            stats=defaultdict(lambda: {"total":0,"correct":0})
            score=0

            for i,q in enumerate(st.session_state.exam_data):
                cat=q["category"]
                stats[cat]["total"]+=1
                st.session_state.exam_stats[cat]["total"]+=1

                if st.session_state.exam_answers.get(i)==q["a"]:
                    score+=1
                    stats[cat]["correct"]+=1
                    st.session_state.exam_stats[cat]["correct"]+=1

            rate=score/40*100

            st.write(f"{score}/40 ({rate:.1f}%)")

            for cat,data in stats.items():
                r=data["correct"]/data["total"]*100
                st.write(f"{cat}:{r:.1f}%")

# =========================
# 弱点分析（統合版）
# =========================
elif st.session_state.page == "analysis":

    if st.button("戻る"):
        st.session_state.page="menu"

    st.write("■ 問題演習")
    for cat,data in st.session_state.practice_stats.items():
        r=data["correct"]/data["total"]*100 if data["total"]>0 else 0
        st.write(f"{cat} ({data['correct']}/{data['total']}) {r:.1f}%")

    st.write("■ 模擬試験")
    for cat,data in st.session_state.exam_stats.items():
        r=data["correct"]/data["total"]*100 if data["total"]>0 else 0
        st.write(f"{cat} ({data['correct']}/{data['total']}) {r:.1f}%")

# =========================
# 復習（完全復活）
# =========================
elif st.session_state.page == "review":

    if st.button("戻る"):
        st.session_state.page="menu"

    if not st.session_state.wrong_log:
        st.write("まだミスなし")
    else:
        for w in st.session_state.wrong_log:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write(w["q"])
            st.write("解説")
            st.write(w["ex"])
            st.markdown('</div>', unsafe_allow_html=True)
