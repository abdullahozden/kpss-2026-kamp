import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import hashlib
from collections import defaultdict
from datetime import datetime

# --- 1. VERİ BAĞLANTISI ---
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

if 'user' not in st.session_state:
    st.session_state.user = None
if 'selected_icon' not in st.session_state:
    st.session_state.selected_icon = "📌"
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
    .q-stats { color: #94a3b8; font-size: 0.85rem; margin-bottom: 5px; }
    .history-item {
        background: #161b22; padding: 10px; border-radius: 8px; 
        margin-bottom: 5px; border: 1px solid #30363d;
    }
    .stPopover button { height: 42px !important; min-width: 50px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GİRİŞ KONTROLÜ ---
all_db = load_all_data()

if st.session_state.user is None:
    st.markdown('<div class="custom-header" style="text-align:center;"><h1>🚀 2026 KPSS Kampı Giriş</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with tab1:
        with st.form("login_f"):
            u_name = st.text_input("Kullanıcı Adı")
            u_pass = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş", use_container_width=True):
                user_check = all_db[(all_db['username'] == u_name) & (all_db['password'] == hash_password(u_pass))]
                if not user_check.empty:
                    st.session_state.user = u_name
                    st.rerun()
                else: st.error("Hatalı bilgiler!")
    
    with tab2:
        with st.form("reg_f"):
            new_u = st.text_input("Yeni Kullanıcı Adı")
            new_p = st.text_input("Yeni Şifre", type="password")
            if st.form_submit_button("Kayıt Ol", use_container_width=True):
                if new_u in all_db['username'].values: st.error("Bu kullanıcı zaten var.")
                else:
                    reg_row = pd.DataFrame([{"username": new_u, "password": hash_password(new_p), "tamamlandi": True, "id": 0, "konu": "Hesap Aktif", "soru_cozulen": 0}])
                    save_to_gsheets(pd.concat([all_db, reg_row], ignore_index=True))
                    st.success("Kayıt başarılı!")
    st.stop()

# --- 4. ANA PROGRAM ---
username = st.session_state.user
user_df = all_db[all_db['username'] == username].copy()

# Sayısal alanları güvenli hale getir
user_df['soru_cozulen'] = pd.to_numeric(user_df['soru_cozulen'], errors='coerce').fillna(0).astype(int)
user_df['soru_hedef'] = pd.to_numeric(user_df['soru_hedef'], errors='coerce').fillna(1).astype(int)

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
            new_ders = st.text_input("Ders Adı", placeholder="Örn: Vatandaşlık", label_visibility="collapsed")
        with c_add2:
            with st.popover(st.session_state.selected_icon, use_container_width=True):
                önerilenler = ["📚", "📐", "🏛️", "🌍", "📰", "⚖️", "🧪", "🧬", "🎨", "💻", "⏰", "💡", "📝", "✅", "🔥"]
                cols = st.columns(4)
                for i, emo in enumerate(önerilenler):
                    if cols[i % 4].button(emo, key=f"e_{i}"):
                        st.session_state.selected_icon = emo
                        st.rerun()
        with c_add3:
            if st.button("Dersi Ekle", use_container_width=True, type="primary"):
                if new_ders:
                    st.session_state.dersler[new_ders] = st.session_state.selected_icon
                    st.rerun()

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        d_secim = st.selectbox("Ders Seçin", list(st.session_state.dersler.keys()))
        k_adi = st.text_input("Konu Adı")
    with c2:
        tarih = st.date_input("Tarih Seçin", format="DD/MM/YYYY")
        s_hedef = st.number_input("Soru Hedefi", min_value=1, value=50)

    v_sayisi = st.select_slider("Video Sayısı", options=range(1, 6), value=1)
    with st.form("new_plan_form"):
        v_urls = [st.text_input(f"Video {i+1} URL", key=f"u_{i}") for i in range(v_sayisi)]
        if st.form_submit_button("Planı Sheets'e Kaydet", use_container_width=True):
            if k_adi:
                v_data = json.dumps([{"url": format_yt_link(u), "done": False} for u in v_urls if u.strip()])
                new_plan = pd.DataFrame([{
                    "username": username, "password": all_db[all_db['username']==username]['password'].values[0],
                    "ders": d_secim, "konu": k_adi, "tarih": str(tarih),
                    "videolar": v_data, "soru_hedef": int(s_hedef), "soru_cozulen": 0,
                    "tamamlandi": False, "id": int(datetime.now().timestamp())
                }])
                save_to_gsheets(pd.concat([all_db, new_plan], ignore_index=True))
                st.success("Plan kaydedildi!")
                st.rerun()

# --- 6. GÜNLÜK PLANIM ---
elif menu == "📅 Günlük Planım":
    col_t, col_tog = st.columns([4, 1])
    with col_t: st.subheader("📅 Görev Takibi")
    with col_tog: show_history = st.toggle("📜 Arşiv")

    user_df['tamamlandi'] = user_df['tamamlandi'].astype(bool)
    display_df = user_df[user_df['tamamlandi'] == show_history]
    
    if display_df.empty:
        st.info("Kayıt bulunamadı.")
    else:
        for idx, row in display_df.iterrows():
            db_idx = all_db[all_db['id'] == row['id']].index[0]
            ikon = st.session_state.dersler.get(row['ders'], "📌")
            with st.expander(f"{ikon} {row['ders']} - {row['konu']}"):
                v_list = json.loads(row['videolar']) if isinstance(row['videolar'], str) else []
                cl, cr = st.columns([4, 1.2])
                with cl:
                    if v_list:
                        st.markdown('<div class="video-scroll-container">', unsafe_allow_html=True)
                        for v_i, v in enumerate(v_list):
                            if not v['done']:
                                st.video(v['url'])
                                if st.button(f"İzlendi", key=f"v_{row['id']}_{v_i}"):
                                    v['done'] = True
                                    all_db.at[db_idx, 'videolar'] = json.dumps(v_list)
                                    save_to_gsheets(all_db); st.rerun()
                            else: st.success(f"Video {v_i+1} tamamlandı.")
                        st.markdown('</div>', unsafe_allow_html=True)
                with cr:
                    cur_q = int(row['soru_cozulen'])
                    new_q = st.number_input("Soru", value=cur_q, key=f"q_{row['id']}")
                    if new_q != cur_q:
                        all_db.at[db_idx, 'soru_cozulen'] = int(new_q)
                        save_to_gsheets(all_db); st.rerun()
                    if st.button("🌟 BİTİR" if not show_history else "⏪ GERİ AL", key=f"f_{row['id']}", use_container_width=True):
                        all_db.at[db_idx, 'tamamlandi'] = not show_history
                        save_to_gsheets(all_db); st.rerun()
                    if st.button("🗑️ Sil", key=f"d_{row['id']}", use_container_width=True):
                        save_to_gsheets(all_db.drop(db_idx)); st.rerun()

# --- 7. BAŞARILARIM (Tasarım Geri Getirildi) ---
elif menu == "🏆 Başarılarım":
    bitenler = user_df[user_df['tamamlandi'] == True]
    st.info(f"🔥 Toplam: {int(bitenler['soru_cozulen'].sum())} Soru | {len(bitenler)} Konu Tamamlandı")
    
    for d, ikon in st.session_state.dersler.items():
        tum_ders_konulari = user_df[user_df['ders'] == d]
        if not tum_ders_konulari.empty:
            biten_ders_konulari = tum_ders_konulari[tum_ders_konulari['tamamlandi'] == True]
            yuzde = int((len(biten_ders_konulari) / len(tum_ders_konulari)) * 100)
            
            st.markdown(f"### {ikon} {d} (%{yuzde})")
            c_m1, c_m2 = st.columns(2)
            c_m1.metric("Biten Konu", f"{len(biten_ders_konulari)}/{len(tum_ders_konulari)}")
            c_m2.metric("Toplam Soru", int(biten_ders_konulari['soru_cozulen'].sum()))
            st.progress(yuzde / 100)
            
            with st.expander("Detaylar", expanded=False):
                for _, b in biten_ders_konulari.iterrows():
                    # Video verisini güvenli oku
                    try: v_data = json.loads(b['videolar'])
                    except: v_data = []
                    izlenen = len([v for v in v_data if v.get('done')])
                    st.markdown(f"""
                        <div class='success-card'>
                            <b>{b['konu']}</b>: {int(b['soru_cozulen'])} soru çözüldü, {izlenen}/{len(v_data)} video izlendi.
                        </div>
                    """, unsafe_allow_html=True)
            st.divider()
