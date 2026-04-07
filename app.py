import streamlit as st
from openai import OpenAI
import random, time
from collections import Counter

client = OpenAI()

# =========================
# UI（完成版）
# =========================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0e1117, #1c1f26);
    color: #ffffff;
}
.stApp { background: transparent; }

h1 { text-align:center; font-weight:700; }

.block-container {
    padding:2rem 3rem;
    border-radius:12px;
    background: rgba(255,255,255,0.02);
}

.stButton button {
    background: linear-gradient(135deg,#4CAF50,#2e7d32);
    color:white !important;
    border-radius:10px;
    padding:10px 18px;
    font-weight:bold;
    border:none;
}

.stButton button:hover {
    transform: scale(1.05);
}

.stRadio > div {
    background: rgba(255,255,255,0.05);
    padding:10px;
    border-radius:8px;
    margin-bottom:6px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 初期化
# =========================
if "page" not in st.session_state:
    st.session_state.page = "menu"

if "wrong_questions" not in st.session_state:
    st.session_state.wrong_questions = []

# =========================
# 問題生成（学科特化）
# =========================
def generate_problem(main):

    problem_type = random.choice(["適切","不適切"])

    prompt = f"""
知的財産管理技能検定2級【学科試験】の問題を1問作成してください。

分野: {main}

【条件】
・実務NG
・知識問題のみ
・簡潔

問題形式：
・最も{problem_type}なもの

■不適切
正しい3つ＋誤り1つ（自然）

■適切
正解1つ＋誤り3つ

【出力】
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

    st.title("知財2級AIアプリ(ver.1.4.5)")

    if st.button("問題演習"):
        st.session_state.page = "practice"

    if st.button("10問チャレンジ"):
        st.session_state.page = "challenge"
        st.session_state.score = 0
        st.session_state.count = 0

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

    if "current" not in st.session_state:
        st.session_state.current = None

    if st.button("問題生成") or st.session_state.current is None:

        raw,ptype = generate_problem(category)

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
            "ptype":ptype
        }
        st.session_state.answered=False
        st.session_state.category=category

    data = st.session_state.current

    if data["ptype"]=="不適切":
        st.markdown("最も <u>不適切</u> を選べ",unsafe_allow_html=True)
    else:
        st.write("最も適切を選べ")

    st.write(data["q"])

    choice = st.radio("選択",data["c"])

    if st.button("回答"):

        st.session_state.answered=True

        if choice[0]==data["a"]:
            st.success("正解")
        else:
            st.error("不正解")
            st.session_state.wrong_questions.append(st.session_state.category)

    if st.session_state.answered:
        st.write("解説")
        st.write(data["ex"])
        st.write("根拠")
        st.info(data["ev"])

# =========================
# 10問チャレンジ
# =========================
elif st.session_state.page == "challenge":

    if st.button("戻る"):
        st.session_state.page = "menu"

    category = st.selectbox("分野",[
        "特許・実用新案","意匠","商標","条約","著作権"
    ])

    if st.session_state.count < 10:

        raw,ptype = generate_problem(category)

        q = raw.split("【選択肢】")[0]
        c = raw.split("【選択肢】")[1].split("【正解】")[0]
        a = raw.split("【正解】")[1].split("【解説】")[0].strip()

        choices = [x for x in c.split("\n") if x]

        st.write(f"{st.session_state.count+1}問目")
        st.write(q)

        choice = st.radio("選択",choices)

        if st.button("回答"):
            st.session_state.count+=1
            if choice[0]==a:
                st.session_state.score+=1

    else:
        rate = st.session_state.score/10*100
        st.write(f"正答率：{rate}%")

# =========================
# 模擬試験
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
                    "a":a
                })

    if st.session_state.exam_started:

        remain=int(3600-(time.time()-st.session_state.start_time))

        if remain<=0:
            st.warning("時間終了")
            finish=True
        else:
            st.write(f"残り{remain//60}分")
            finish=False

        for i,q in enumerate(st.session_state.exam_data):
            st.write(f"Q{i+1}")
            st.write(q["q"])
            ch=st.radio("選択",q["c"],key=f"ex{i}")
            st.session_state.exam_answers[i]=ch[0]

        if st.button("試験終了") or finish:

            score=sum(
                1 for i,q in enumerate(st.session_state.exam_data)
                if st.session_state.exam_answers.get(i)==q["a"]
            )

            rate=score/40*100

            st.title("結果")
            st.write(f"{score}/40")
            st.write(f"{rate:.1f}%")

            if rate>=80:
                st.success("合格")
            else:
                st.error("不合格")

# =========================
# 分析
# =========================
elif st.session_state.page == "analysis":

    if st.button("戻る"):
        st.session_state.page="menu"

    if not st.session_state.wrong_questions:
        st.write("データ不足")
    else:
        counter=Counter(st.session_state.wrong_questions)

        for k,v in counter.most_common():
            st.write(f"{k}:{v}")

        text="\n".join([f"{k}:{v}" for k,v in counter.items()])

        res=client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{"role":"user","content":f"{text}の弱点分析"}]
        )

        st.write(res.choices[0].message.content)

# =========================
# 復習
# =========================
elif st.session_state.page == "review":

    if st.button("戻る"):
        st.session_state.page="menu"

    st.write(st.session_state.wrong_questions)
