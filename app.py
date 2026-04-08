import streamlit as st
from openai import OpenAI
import json
import random
from collections import defaultdict

client = OpenAI()

# =========================
# 初期化（安全設計）
# =========================
def init():
    defaults = {
        "page":"menu",

        # 共通
        "selected_category":None,
        "show_category":False,

        # 問題演習
        "practice_q":None,
        "practice_answered":False,
        "practice_result":None,

        # 復習
        "wrong_questions":[],
        "review_index":0,

        # 模試
        "exam_index":0,
        "exam_q":None,
        "exam_done":False,
        "exam_stats":defaultdict(lambda: {"total":0,"correct":0}),
    }

    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

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
# 問題生成（安定）
# =========================
def clean(text):
    return text.split(".",1)[-1].strip()

def generate(cat):
    try:
        res = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{
                "role":"user",
                "content":f"""
分野:{cat}
知財2級学科問題を作れ

条件:
・4択
・正解1つ
・選択肢に記号つけるな
・各選択肢理由書け

JSON:
{{
"question":"",
"choices":["","","",""],
"answer":"A",
"choice_explanations":{{"A":"","B":"","C":"","D":""}}
}}
"""
            }],
            response_format={"type":"json_object"}
        )

        data = json.loads(res.choices[0].message.content)

        choices = [clean(c) for c in data["choices"]]
        correct = choices[0]

        random.shuffle(choices)
        labels = ["A","B","C","D"]

        mapping = dict(zip(labels, choices))

        for k,v in mapping.items():
            if v == correct:
                answer = k

        return {
            "cat":cat,
            "question":data["question"],
            "choices":[f"{k}. {v}" for k,v in mapping.items()],
            "answer":answer,
            "exp":data["choice_explanations"]
        }

    except:
        return {
            "cat":cat,
            "question":"生成失敗",
            "choices":["A.-","B.-","C.-","D.-"],
            "answer":"A",
            "exp":{"A":"-","B":"-","C":"-","D":"-"}
        }

# =========================
# 共通UI
# =========================
def go(p): st.session_state.page = p

def select(cat):
    st.session_state.selected_category = cat
    st.session_state.show_category = False
    st.rerun()

# =========================
# メニュー
# =========================
if st.session_state.page == "menu":

    st.title("知財2級学科AIサイト(ver.1.8.0)")

    st.button("問題演習", on_click=go, args=("practice",))
    st.button("模擬試験", on_click=go, args=("exam",))
    st.button("復習", on_click=go, args=("review",))

# =========================
# 問題演習
# =========================
elif st.session_state.page == "practice":

    st.button("戻る", on_click=go, args=("menu",))

    if st.button("分野選択"):
        st.session_state.show_category = not st.session_state.show_category

    if st.session_state.show_category:
        for c in CATEGORIES:
            st.button(c, on_click=select, args=(c,))

    if st.session_state.selected_category:
        st.write(f"### {st.session_state.selected_category}")

        if st.button("問題生成"):
            st.session_state.practice_q = generate(st.session_state.selected_category)
            st.session_state.practice_answered = False

    if st.session_state.practice_q:

        q = st.session_state.practice_q
        st.write(q["question"])

        choice = st.radio("", q["choices"])

        if st.button("回答"):
            st.session_state.practice_answered = True

            if choice.startswith(q["answer"]):
                st.session_state.practice_result = "ok"
            else:
                st.session_state.practice_result = "ng"
                st.session_state.wrong_questions.append({"data":q,"mode":"practice"})

        if st.session_state.practice_answered:

            if st.session_state.practice_result == "ok":
                st.success(f"正解（{q['answer']}）")
            else:
                st.error(f"不正解（正解:{q['answer']}）")

            for k in ["A","B","C","D"]:
                st.write(f"{k}: {q['exp'][k]}")

# =========================
# 模試
# =========================
elif st.session_state.page == "exam":

    st.button("戻る", on_click=go, args=("menu",))

    if not st.session_state.exam_q:
        if st.button("試験開始"):
            st.session_state.exam_index = 0
            st.session_state.exam_done = False
            st.session_state.exam_stats = defaultdict(lambda: {"total":0,"correct":0})
            st.session_state.exam_q = generate(random.choice(CATEGORIES))
            st.rerun()

    elif not st.session_state.exam_done:

        q = st.session_state.exam_q
        st.write(f"Q{st.session_state.exam_index+1}/40")
        st.write(q["question"])

        choice = st.radio("", q["choices"], key=f"exam{st.session_state.exam_index}")

        if st.button("次へ"):

            cat = q["cat"]
            st.session_state.exam_stats[cat]["total"] += 1

            if choice.startswith(q["answer"]):
                st.session_state.exam_stats[cat]["correct"] += 1
            else:
                st.session_state.wrong_questions.append({"data":q,"mode":"exam"})

            st.session_state.exam_index += 1

            if st.session_state.exam_index >= 40:
                st.session_state.exam_done = True
            else:
                st.session_state.exam_q = generate(random.choice(CATEGORIES))

            st.rerun()

    else:
        stats = st.session_state.exam_stats

        total = sum(v["correct"] for v in stats.values())
        total_q = sum(v["total"] for v in stats.values())
        rate = (total/total_q*100) if total_q else 0

        st.write(f"## 結果 {total}/{total_q}")
        st.write(f"正答率 {rate:.1f}%")

        if total >= 32:
            st.success("合格")
        else:
            st.error("不合格")

        st.write("### 分野別")
        for k,v in stats.items():
            t = v["total"]
            c = v["correct"]
            r = (c/t*100) if t else 0
            st.write(f"{k}: {c}/{t} ({r:.1f}%)")

# =========================
# 復習
# =========================
elif st.session_state.page == "review":

    st.button("戻る", on_click=go, args=("menu",))

    if not st.session_state.wrong_questions:
        st.write("なし")

    else:
        q = st.session_state.wrong_questions[0]["data"]

        st.write(q["question"])

        choice = st.radio("", q["choices"])

        if st.button("回答"):

            if choice.startswith(q["answer"]):
                st.success("正解")
                st.session_state.wrong_questions.pop(0)
                st.rerun()
            else:
                st.error(f"不正解（正解:{q['answer']}）")

                for k in ["A","B","C","D"]:
                    st.write(f"{k}: {q['exp'][k]}")
