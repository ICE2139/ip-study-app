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
# 出題範囲（学科）
# =========================
SCOPE = {
"特許・実用新案":"明細書、補正、拒絶理由通知、審判、特許要件、新規性、進歩性、出願手続、存続期間",
"商標":"登録要件、識別力、不登録事由、効力、更新、審判",
"著作権":"著作物、人格権、権利内容、保護期間、利用許諾、侵害",
"条約":"パリ条約、TRIPS、マドリッド、優先権",
"意匠":"登録要件、類似、存続期間",
"不正競争防止法":"周知表示、営業秘密",
"民法":"契約、意思表示",
"独占禁止法":"不公正な取引方法",
"種苗法":"品種登録",
"関税法":"輸入差止",
"外為法":"技術輸出規制",
"弁理士法":"業務"
}

# =========================
# 出題比重
# =========================
WEIGHTS = {
"特許・実用新案":27,
"著作権":21,
"商標":13,
"条約":6,
"意匠":3,
"不正競争防止法":3,
"民法":2,
"独占禁止法":2,
"種苗法":1,
"関税法":1,
"外為法":1,
"弁理士法":0.5
}

def pick_category():
    cats = list(WEIGHTS.keys())
    weights = [w * random.uniform(0.9,1.1) for w in WEIGHTS.values()]
    return random.choices(cats, weights=weights, k=1)[0]

# =========================
# A〜D変換
# =========================
def to_label(i):
    return ["A","B","C","D"][i]

label_to_index = {"A":0,"B":1,"C":2,"D":3}

# =========================
# 問題生成（最強版）
# =========================
def generate(cat):
    try:
        scope = SCOPE.get(cat,"")

        res = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{
                "role":"user",
                "content":f"""
分野:{cat}

出題範囲:
{scope}

知財2級 学科試験問題を作成せよ

条件:
・4択
・正解は必ず1つ
・問題文に選択肢を書かない
・条文知識ベース
・「適切なものを選べ」形式
・選択肢は明確に正誤が分かれる
・曖昧禁止

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

        choices, exps = [], []
        ans = None

        for i,(c,e) in enumerate(items):
            choices.append(c)
            exps.append(e)
            if (c,e)==correct:
                ans = i

        return {"cat":cat,"q":data["question"],"choices":choices,"exps":exps,"ans":ans}

    except:
        return {"cat":cat,"q":"生成失敗","choices":["-"]*4,"exps":["-"]*4,"ans":0}

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
    st.title("知財2級学科AIサイト(ver.1.8.3)")
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
            st.session_state.exam_q=generate(pick_category())

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
                st.session_state.exam_q=generate(pick_category())

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
