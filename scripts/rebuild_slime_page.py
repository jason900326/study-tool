from pathlib import Path
import re

p=Path('streamlit_app.py')
s=p.read_text(encoding='utf-8').replace('青蘋果史萊姆','綠色史萊姆')

catalog='''SLIME_CATALOG = [
{"name":"綠色史萊姆","emoji":"🟢","rarity":"N","theme":"green","tagline":"最經典的 MedSlime 夥伴。","weight":8,"accessory":"嫩芽髮夾"},
{"name":"藍色史萊姆","emoji":"🔵","rarity":"N","theme":"blue","tagline":"安靜又可靠的讀書夥伴。","weight":8,"accessory":"水滴小帽"},
{"name":"黃色史萊姆","emoji":"🟡","rarity":"N","theme":"yellow","tagline":"像一顆精神滿滿的小太陽。","weight":8,"accessory":"太陽眼鏡"},
{"name":"粉色史萊姆","emoji":"🩷","rarity":"N","theme":"pink","tagline":"軟綿綿又親人的陪伴型史萊姆。","weight":8,"accessory":"愛心髮夾"},
{"name":"拿鐵史萊姆","emoji":"☕","rarity":"R","theme":"latte","tagline":"早八時特別可靠。","weight":6.3333,"accessory":"拉花小帽"},
{"name":"漢堡史萊姆","emoji":"🍔","rarity":"R","theme":"burger","tagline":"肚子餓時請不要盯太久。","weight":6.3333,"accessory":"薯條髮箍"},
{"name":"壽司史萊姆","emoji":"🍣","rarity":"R","theme":"sushi","tagline":"頭頂總像多放了一片鮭魚。","weight":6.3333,"accessory":"醬油小瓶"},
{"name":"珍珠奶茶史萊姆","emoji":"🧋","rarity":"R","theme":"boba","tagline":"移動時珍珠也會跟著晃。","weight":6.3333,"accessory":"粗吸管"},
{"name":"飯糰史萊姆","emoji":"🍙","rarity":"R","theme":"onigiri","tagline":"樸素但很可靠的補充能量夥伴。","weight":6.3333,"accessory":"海苔披風"},
{"name":"章魚燒史萊姆","emoji":"🐙","rarity":"R","theme":"takoyaki","tagline":"總是熱呼呼的。","weight":6.3335,"accessory":"柴魚片帽"},
{"name":"失眠史萊姆","emoji":"🥱","rarity":"SR","theme":"insomnia","tagline":"熬夜讀書的最佳夥伴。","weight":4.5,"accessory":"失眠眼罩"},
{"name":"融化史萊姆","emoji":"🫠","rarity":"SR","theme":"melted","tagline":"讀到腦袋停止運作時的樣子。","weight":4.5,"accessory":"冰敷袋"},
{"name":"靈魂出竅史萊姆","emoji":"👻","rarity":"SR","theme":"outofbody","tagline":"身體還在書桌前，靈魂先下課了。","weight":4.5,"accessory":"幽靈光環"},
{"name":"爆哭史萊姆","emoji":"😭","rarity":"SR","theme":"crying","tagline":"看到錯題數量時通常比你先哭。","weight":4.5,"accessory":"超大面紙"},
{"name":"404史萊姆","emoji":"💾","rarity":"SR","theme":"error404","tagline":"Knowledge not found.","weight":4.5,"accessory":"404警告牌"},
{"name":"厭世史萊姆","emoji":"😑","rarity":"SR","theme":"deadinside","tagline":"今天也沒有特別想努力。","weight":4.5,"accessory":"厭世咖啡杯"},
{"name":"Chill史萊姆","emoji":"😎","rarity":"SSR","theme":"chill","tagline":"不用急，該讀的還是會讀完。","weight":3,"accessory":"Chill墨鏡"},
]'''
s,n=re.subn(r'SLIME_CATALOG = \[.*?\]\n\nSLIME_BY_NAME =',catalog+'\n\nSLIME_BY_NAME =',s,count=1,flags=re.S)
assert n==1

page='''def slime_page():
    topbar()
    render_back_button("返回首頁", "home", "back_slime")
    names={x["name"] for x in SLIME_CATALOG}
    st.session_state.collection=[x for x in st.session_state.collection if x in names]
    if "綠色史萊姆" not in st.session_state.collection: st.session_state.collection.insert(0,"綠色史萊姆")
    if st.session_state.selected_slime not in st.session_state.collection: st.session_state.selected_slime="綠色史萊姆"
    st.session_state.setdefault("slime_detail_name",st.session_state.selected_slime)
    st.session_state.setdefault("slime_sort","稀有度")
    st.session_state.setdefault("slime_accessories",{})
    for x in SLIME_CATALOG: st.session_state.slime_progress.setdefault(x["name"],{}).setdefault("fragments",0)

    st.markdown("## 史萊姆圖鑑")
    st.caption("收集史萊姆、累積專屬碎片並解鎖外觀飾品。史萊姆只提供陪伴與展示，不提供能力 Buff。")
    a,b=st.columns([2,1])
    with a:
        filt=st.radio("稀有度",["全部","N","R","SR","SSR"],horizontal=True,label_visibility="collapsed")
    with b:
        sort=st.selectbox("排序",["稀有度","最近取得","是否擁有","碎片數"],label_visibility="collapsed")
    st.caption(f"🪙 {st.session_state.coins:,}　🎟️ {st.session_state.tickets:,}")

    visible=[x for x in SLIME_CATALOG if filt=="全部" or x["rarity"]==filt]
    rank={"SSR":0,"SR":1,"R":2,"N":3}
    if sort=="稀有度": visible.sort(key=lambda x:(rank[x["rarity"]],x["name"]))
    elif sort=="是否擁有": visible.sort(key=lambda x:(x["name"] not in st.session_state.collection,rank[x["rarity"]]))
    elif sort=="碎片數": visible.sort(key=lambda x:-st.session_state.slime_progress[x["name"]]["fragments"])
    elif sort=="最近取得": visible.sort(key=lambda x:(x["name"] not in st.session_state.collection,-st.session_state.collection.index(x["name"]) if x["name"] in st.session_state.collection else 0))

    left,right=st.columns([2.1,1],gap="large")
    with left:
        for start in range(0,len(visible),5):
            cols=st.columns(5)
            for i,col in enumerate(cols):
                if start+i>=len(visible): continue
                x=visible[start+i]; owned=x["name"] in st.session_state.collection
                title="???" if x["rarity"]=="SSR" and not owned else x["name"]
                frag=st.session_state.slime_progress[x["name"]]["fragments"]
                with col:
                    st.markdown(f"### {'🔒' if not owned else x['emoji']}\n**{title}** · {x['rarity']}")
                    st.caption("已擁有" if owned else "尚未取得")
                    if owned: st.progress(min(1.0,frag/30),text=f"碎片 {frag} / 30")
                    if st.button("查看詳情",key=f"slime_v2_{x['theme']}",use_container_width=True):
                        st.session_state.slime_detail_name=x["name"]; st.rerun()
    with right:
        x=SLIME_BY_NAME.get(st.session_state.slime_detail_name,SLIME_CATALOG[0]); owned=x["name"] in st.session_state.collection
        title="???" if x["rarity"]=="SSR" and not owned else x["name"]
        st.markdown(f"# {x['emoji'] if owned else '🔒'}")
        st.markdown(f"### {title}　`{x['rarity']}`")
        st.write(x["tagline"] if owned or x["rarity"]!="SSR" else "取得後才會揭曉真正身分。")
        if owned:
            if x["name"]==st.session_state.selected_slime: st.button("✓ 目前陪伴中",disabled=True,use_container_width=True)
            elif st.button("設為陪伴史萊姆",type="primary",use_container_width=True): st.session_state.selected_slime=x["name"]; st.rerun()
            frag=st.session_state.slime_progress[x["name"]]["fragments"]
            st.markdown("#### 專屬碎片"); st.progress(min(1.0,frag/30),text=f"{frag} / 30")
            need=max(0,(30-frag+9)//10)
            st.caption("已可解鎖專屬飾品" if frag>=30 else f"再取得 {need} 次重複角色即可解鎖專屬飾品")
            acc=st.session_state.slime_accessories.setdefault(x["name"],False)
            st.markdown(f"#### 專屬飾品\n✨ **{x['accessory']}**")
            if not acc:
                if st.button("解鎖專屬飾品",disabled=frag<30,use_container_width=True):
                    st.session_state.slime_progress[x["name"]]["fragments"]-=30; st.session_state.slime_accessories[x["name"]]=True; st.rerun()
            else: st.success("已解鎖")
        else: st.info("取得這隻史萊姆後，即可累積專屬碎片、設為陪伴並解鎖專屬飾品。")

    owned=len([x for x in SLIME_CATALOG if x["name"] in st.session_state.collection])
    st.divider(); st.markdown("### 收藏進度"); st.progress(owned/17,text=f"{owned} / 17")
    cols=st.columns(4)
    for c,r in zip(cols,["N","R","SR","SSR"]):
        got=sum(1 for x in SLIME_CATALOG if x["rarity"]==r and x["name"] in st.session_state.collection); total=sum(1 for x in SLIME_CATALOG if x["rarity"]==r)
        c.metric(r,f"{got} / {total}")
    st.caption(f"專屬飾品：{sum(1 for v in st.session_state.slime_accessories.values() if v)} / 17")
'''
s,n=re.subn(r'def slime_page\(\):.*?\n\ndef achievements_page\(\):',page+'\n\ndef achievements_page():',s,count=1,flags=re.S)
assert n==1
p.write_text(s,encoding='utf-8')
