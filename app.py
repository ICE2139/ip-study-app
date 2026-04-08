import streamlit as st
from openai import OpenAI
import json
import random
from collections import defaultdict

client = OpenAI()

# =========================
# 初期化
# =========================
def init():
    defaults = {
        "page":"menu",
        "category":None,
        "show_cat":False,

        "practice_q":None,
        "practice_answered":False,

        "wrong":[],
        
        "exam_q":None,
        "exam_i":0,
        "exam_done":False,
        "exam_stats":defaultdict(lambda: {"t":0,"c":0}),
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k]=v

init()

# =========================
# 分野
# =========================
CATS = [
    "特許・実用新案","意匠","商標","条約",
    "著作権","不正競争防止法","民法",
    "独占禁止法","種苗法","関税法","外為法","弁理士法"
]

# =========================
# A〜D変換
# =========================
def to_label(i):
    return ["A","B","C","D"][i]

label_to_index = {"A":0,"B":1,"C":2,"D":3}

# =========================
# 問題生成（完全安定）
# =========================
def generate(cat):
    try:
        res = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{
                "role":"user",
                "content":f"""
分野:{cat}

知財2級 学科問題

条件:
・4択
・正解1つ
・問題文に選択肢を書かない
・選択肢に記号つけない

JSON:
{{
"question":"",
"choices":["","","",""],
"answer_index":0,
"explanations":["","","",""]
}}
"""
            }],
            response_format={"type":"json_object"}
        )

        data = json.loads(res.choices[0].message.content)

        items = list(zip(data["choices"], data["explanations"]))
        correct = items[data["answer_index"]]

        random.shuffle(items)

        choices = []
        exps = []
        ans = None

        for i,(c,e) in enumerate(items):
            choices.append(c)
            exps.append(e)
            if (c,e)==correct:
                ans = i

        return {
            "cat":cat,
            "q":data["question"],
            "choices":choices,
            "exps":exps,
            "ans":ans
        }

    except:
        return {
            "cat":cat,
            "q":"生成失敗",
            "choices":["-","-","-","-"],
            "exps":["-","-","-","-"],
            "ans":0
        }

# =========================
# UI関数
# =========================
def go(p): st.session_state.page=p

def select(cat):
    st.session_state.category=cat
    st.session_state.show_cat=False

# =========================
# メニュー
# =========================
if st.session_state.page=="menu":

    st.title("知財2級学科AIサイト(ver.1.8.2)")

    st.button("問題演習",on_click=go,args=("p",))
    st.button("模擬試験",on_click=go,args=("e",))
    st.button("復習",on_click=go,args=("r",))

# =========================
# 問題演習
# =========================
elif st.session_state.page=="p":

    st.button("戻る",on_click=go,args=("menu",))

    if st.button("分野選択"):
        st.session_state.show_cat=not st.session_state.show_cat

    if st.session_state.show_cat:
        for c in CATS:
            st.button(c,on_click=select,args=(c,))

    if st.session_state.category:
        st.write(f"### {st.session_state.category}")

        if st.button("問題生成"):
            st.session_state.practice_q = generate(st.session_state.category)
            st.session_state.practice_answered=False

    q = st.session_state.practice_q

    if q:
        st.write(q["q"])

        options = [f"{to_label(i)}. {c}" for i,c in enumerate(q["choices"])]
        choice = st.radio("", options)

        if st.button("回答"):
            st.session_state.practice_answered=True

            selected = label_to_index[choice[0]]

            if selected == q["ans"]:
                st.success(f"正解（{to_label(q['ans'])}）")
            else:
                st.error(f"不正解（正解：{to_label(q['ans'])}）")
                st.session_state.wrong.append({"data":q,"mode":"practice"})

        if st.session_state.practice_answered:
            for i,e in enumerate(q["exps"]):
                st.write(f"{to_label(i)}: {e}")

# =========================
# 模試
# =========================
elif st.session_state.page=="e":

    st.button("戻る",on_click=go,args=("menu",))

    if not st.session_state.exam_q:
        if st.button("試験開始"):
            st.session_state.exam_i=0
            st.session_state.exam_done=False
            st.session_state.exam_stats=defaultdict(lambda: {"t":0,"c":0})
            st.session_state.exam_q=generate(random.choice(CATS))

    elif not st.session_state.exam_done:

        q = st.session_state.exam_q

        st.write(f"Q{st.session_state.exam_i+1}/40")
        st.write(q["q"])

        options = [f"{to_label(i)}. {c}" for i,c in enumerate(q["choices"])]
        choice = st.radio("", options, key=f"ex{st.session_state.exam_i}")

        if st.button("次へ"):

            selected = label_to_index[choice[0]]

            cat = q["cat"]
            st.session_state.exam_stats[cat]["t"]+=1

            if selected == q["ans"]:
                st.session_state.exam_stats[cat]["c"]+=1
            else:
                st.session_state.wrong.append({"data":q,"mode":"exam"})

            st.session_state.exam_i+=1

            if st.session_state.exam_i>=40:
                st.session_state.exam_done=True
            else:
                st.session_state.exam_q=generate(random.choice(CATS))

            st.rerun()

    else:
        stats=st.session_state.exam_stats

        total=sum(v["c"] for v in stats.values())
        total_q=sum(v["t"] for v in stats.values())

        rate=(total/total_q*100) if total_q else 0

        st.write(f"## 結果 {total}/{total_q}")
        st.write(f"正答率 {rate:.1f}%")

        if total>=32:
            st.success("合格")
        else:
            st.error("不合格")

        st.write("### 分野別")
        for k,v in stats.items():
            t=v["t"];c=v["c"]
            r=(c/t*100) if t else 0
            st.write(f"{k}: {c}/{t} ({r:.1f}%)")

# =========================
# 復習
# =========================
elif st.session_state.page=="r":

    st.button("戻る",on_click=go,args=("menu",))

    if not st.session_state.wrong:
        st.write("なし")

    else:
        q = st.session_state.wrong[0]["data"]

        st.write(f"【{st.session_state.wrong[0]['mode']}】")
        st.write(q["q"])

        options = [f"{to_label(i)}. {c}" for i,c in enumerate(q["choices"])]
        choice = st.radio("", options)

        if st.button("回答"):

            selected = label_to_index[choice[0]]

            if selected==q["ans"]:
                st.success("正解")
                st.session_state.wrong.pop(0)
                st.rerun()
            else:
                st.error(f"不正解（正解：{to_label(q['ans'])}）")
                for i,e in enumerate(q["exps"]):
                    st.write(f"{to_label(i)}: {e}")
