import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import hashlib
from datetime import datetime

# --- 1. VERİ BAĞLANTISI VE FONKSİYONLAR ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_data():
    try:
        df = conn.read(ttl=0)
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=["username", "password", "ders", "konu", "tarih", "videolar", "soru_hedef", "soru_cozulen", "tamamlandi", "id"])

def save_to_gsheets(df):
    conn.update(data=df)
    st.cache_data.clear()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def format_yt_link(url):
    url = url.strip()
    return url if url.startswith("http") else f"https://{url}" if url else ""

# --- 2. TASARIM AYARLARI ---
st.set_page_config(page_title="2026 KPSS Kampım", layout="wide", page_icon="🎓")

# Session State Başlatma
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_icon' not in st.session_state: st.session_state.selected_icon = "📌"
if 'dersler' not in st.session_state:
    st.session_state.dersler = {"Matematik": "📐", "Türkçe": "📚", "Tarih": "🏛️", "Coğrafya": "🌍", "Güncel Bilgiler": "📰"}

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .custom-header {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        padding: 1.5rem; border-radius: 15px; border-left: 8px solid #3b82f6; margin-bottom: 2rem;
    }
    .video-scroll-container {
        max-height: 450px; overflow-y: auto; padding: 15px;
        background: #0d1117; border-radius: 12px; border: 1px solid #30363D;
    }
    .success-card {
        background-color: #1c2128; border: 1px solid #238636; padding: 12px;
        border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #238636;
    }
    .history-item {
        background: #161b22; padding: 12px; border-radius: 8px; 
        margin-bottom: 8px; border: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center;
    }
    .stPopover button { height: 42px !important; min-width: 50px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GİRİŞ & VERİ ÇEKME ---
all_db = load_all_data()

if st.session_state.user is None:
    st.markdown('<div class="custom-header" style="text-align:center;"><h1>🚀 2026 KPSS Kampı Giriş</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t1:
        with st.form("l_f"):
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                user_check = all_db[(all_db['username'] == u) & (all_db['password'] == hash_password(p))]
                if not user_check.empty:
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Hatalı giriş!")
    with t2:
        with st.form("r_f"):
            nu = st.text_input("Yeni Kullanıcı Adı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.form_submit_button("Kayıt Ol", use_container_width=True):
                if nu in all_db['username'].values: st.error("Bu kullanıcı mevcut.")
                else:
                    new_u_row = pd.DataFrame([{"username": nu, "password": hash_password(np), "tamamlandi": True, "id": 0, "konu": "Hesap Aktif", "soru_cozulen": 0}])
                    save_to_gsheets(pd.concat([all_db, new_u_row], ignore_index=True))
                    st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
    st.stop()

# Veri Hazırlama
username = st.session_state.user
# Tip dönüşümlerini garantiye al
all_db['tamamlandi'] = all_db['tamamlandi'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, '1.0': True, '0.0': False})
all_db['id'] = pd.to_numeric(all_db['id'], errors='coerce').fillna(0).astype(int)
all_db['soru_cozulen'] = pd.to_numeric(all_db['soru_cozulen'], errors='coerce').fillna(0).astype(int)

user_df = all_db[all_db['username'] == username].copy()

# --- 4. KENAR MENÜ ---
st.sidebar.markdown(f"👤 Hoş geldin, **{username}**")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.user = None
    st.rerun()

menu = st.sidebar.radio("Menü", ["📅 Günlük Planım", "📝 Plan Oluştur", "🏆 Başarılarım"])
st.markdown('<div class="custom-header"><h1>🚀 <span style="color: #3b82f6;">2026 KPSS</span> KAMPIM</h1></div>', unsafe_allow_html=True)

# --- 5. PLAN OLUŞTUR ---
if menu == "📝 Plan Oluştur":
    st.subheader("📝 Yeni Plan")
    with st.expander("➕ Yeni Ders Ekle", expanded=True):
        c_add1, c_add2, c_add3 = st.columns([5, 1, 1.5])
        with c_add1:
            n_d = st.text_input("Ders Adı", placeholder="Örn: Vatandaşlık", label_visibility="collapsed")
        with c_add2:
            with st.popover(st.session_state.selected_icon, use_container_width=True):
                emos = ["📚", "📐", "🏛️", "🌍", "📰", "⚖️", "🧪", "🎨", "💻", "⏰", "💡", "📝", "✅", "🔥"]
                cols = st.columns(4)
                for i, emo in enumerate(emos):
                    if cols[i % 4].button(emo, key=f"emo_{i}"):
                        st.session_state.selected_icon = emo
                        st.rerun()
        with c_add3:
            if st.button("Dersi Ekle", use_container_width=True, type="primary"):
                if n_d: st.session_state.dersler[n_d] = st.session_state.selected_icon; st.rerun()

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        d_s = st.selectbox("Ders Seçin", list(st.session_state.dersler.keys()))
        k_a = st.text_input("Konu Adı")
    with c2:
        t_r = st.date_input("Tarih Seçin", format="DD/MM/YYYY")
        s_h = st.number_input("Soru Hedefi", min_value=1, value=50)

    v_s = st.select_slider("Video Sayısı", options=range(1, 6), value=1)
    with st.form("n_p_f"):
        v_u = [st.text_input(f"Video {i+1} URL", key=f"u_{i}") for i in range(v_s)]
        if st.form_submit_button("Planı Kaydet", use_container_width=True):
            if k_a:
                v_d = json.dumps([{"url": format_yt_link(u), "done": False} for u in v_u if u.strip()])
                n_p = pd.DataFrame([{
                    "username": username, "password": user_df['password'].values[0],
                    "ders": d_s, "konu": k_a, "tarih": str(t_r), "videolar": v_d,
                    "soru_hedef": int(s_h), "soru_cozulen": 0, "tamamlandi": False, "id": int(datetime.now().timestamp())
                }])
                save_to_gsheets(pd.concat([all_db, n_p], ignore_index=True))
                st.success("Kaydedildi!"); st.rerun()

# --- 6. GÜNLÜK PLANIM (Arşiv Düzenlendi) ---
elif menu == "📅 Günlük Planım":
    col_t, col_tog = st.columns([4, 1])
    with col_t: st.subheader("📅 Görev Takibi")
    with col_tog: show_history = st.toggle("📜 Arşiv")

    display_df = user_df[user_df['tamamlandi'] == show_history]
    
    if show_history:
        for idx, row in display_df.sort_values(by="tarih", ascending=False).iterrows():
            with st.container():
                st.markdown(f"""
                <div class="history-item">
                    <span>✅ {row['tarih']} - <b>{row['ders']}</b>: {row['konu']} ({row['soru_cozulen']} Soru)</span>
                </div>
                """, unsafe_allow_html=True)
                c_h1, c_h2, _ = st.columns([1, 1, 3])
                if c_h1.button("⏪ Geri Al", key=f"rev_{row['id']}"):
                    all_db.loc[all_db['id'] == row['id'], 'tamamlandi'] = False
                    save_to_gsheets(all_db); st.rerun()
                if c_h2.button("🗑️ Sil", key=f"del_{row['id']}"):
                    save_to_gsheets(all_db[all_db['id'] != row['id']]); st.rerun()
        st.divider()

    else:
        if display_df.empty: st.info("Aktif görev yok.")
        for idx, row in display_df.iterrows():
            ikon = st.session_state.dersler.get(row['ders'], "📌")
            with st.expander(f"{ikon} {row['ders']} - {row['konu']}"):
                v_l = json.loads(row['videolar']) if isinstance(row['videolar'], str) else []
                cl, cr = st.columns([4, 1.2])
                with cl:
                    if v_l:
                        st.markdown('<div class="video-scroll-container">', unsafe_allow_html=True)
                        for v_i, v in enumerate(v_l):
                            if not v['done']:
                                st.video(v['url'])
                                if st.button(f"İzlendi ✅", key=f"v_{row['id']}_{v_i}"):
                                    v['done'] = True
                                    all_db.loc[all_db['id'] == row['id'], 'videolar'] = json.dumps(v_l)
                                    save_to_gsheets(all_db); st.rerun()
                            else: st.success(f"Video {v_i+1} Tamam!")
                        st.markdown('</div>', unsafe_allow_html=True)
                with cr:
                    n_q = st.number_input("Soru", value=int(row['soru_cozulen']), key=f"q_{row['id']}")
                    if n_q != row['soru_cozulen']:
                        all_db.loc[all_db['id'] == row['id'], 'soru_cozulen'] = int(n_q)
                        save_to_gsheets(all_db); st.rerun()
                    if st.button("🌟 BİTİR", key=f"f_{row['id']}", use_container_width=True, type="primary"):
                        all_db.loc[all_db['id'] == row['id'], 'tamamlandi'] = True
                        save_to_gsheets(all_db); st.balloons(); st.rerun()

# --- 7. BAŞARILARIM ---
elif menu == "🏆 Başarılarım":
    bitenler = user_df[user_df['tamamlandi'] == True]
    st.info(f"🔥 Toplam: {int(bitenler['soru_cozulen'].sum())} Soru | {len(bitenler)} Konu")
    
    for d, ikon in st.session_state.dersler.items():
        ders_df = user_df[user_df['ders'] == d]
        if not ders_df.empty:
            b_df = ders_df[ders_df['tamamlandi'] == True]
            y = int((len(b_df)/len(ders_df))*100)
            st.markdown(f"### {ikon} {d} (%{y})")
            c_a, c_b = st.columns(2)
            c_a.metric("Biten", f"{len(b_df)}/{len(ders_df)}")
            c_b.metric("Soru", int(b_df['soru_cozulen'].sum()))
            st.progress(y/100)
            with st.expander("Detaylar"):
                for _, b in b_df.iterrows():
                    st.markdown(f"<div class='success-card'><b>{b['konu']}</b>: {int(b['soru_cozulen'])} soru çözüldü.</div>", unsafe_allow_html=True)
