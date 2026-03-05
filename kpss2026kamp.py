import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import hashlib
from datetime import datetime
import time

# --- 1. VERİ BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_data():
    try:
        df = conn.read(ttl=60)
        if df is None or df.empty:
            return pd.DataFrame(columns=["username", "password", "ders", "konu", "tarih", "videolar", "soru_hedef", "soru_cozulen", "tamamlandi", "id"])
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=["username", "password", "ders", "konu", "tarih", "videolar", "soru_hedef", "soru_cozulen", "tamamlandi", "id"])

def save_to_gsheets(df):
    try:
        conn.update(data=df)
        st.cache_data.clear()
        time.sleep(0.5)
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def format_yt_link(url):
    url = url.strip()
    return url if url.startswith("http") else f"https://{url}" if url else ""

# --- 2. TASARIM AYARLARI ---
st.set_page_config(page_title="2026 KPSS ÇALIŞMA PLANI", layout="wide", page_icon="🎓")

if 'user' not in st.session_state: st.session_state.user = None
if 'selected_icon' not in st.session_state: st.session_state.selected_icon = "📌"
if 'dersler' not in st.session_state:
    st.session_state.dersler = {"Matematik": "📐", "Türkçe": "📚", "Tarih": "🏛️", "Coğrafya": "🌍", "Güncel Bilgiler": "📰"}

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    [data-testid="stSidebarNav"] span { font-size: 1.2rem !important; font-weight: 600 !important; }
    .custom-header {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 2rem; border-radius: 20px; border-bottom: 4px solid #3b82f6;
        margin-bottom: 2rem; text-align: center;
    }
    .stExpander { background-color: #161b22 !important; border: 1px solid #30363d !important; border-radius: 12px !important; margin-bottom: 1rem !important; }
    .video-container { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 10px; overflow: hidden; }
    .video-label-bar { background-color: #1c2128; color: #58a6ff; padding: 4px 8px; font-size: 0.85rem; font-weight: 700; text-align: center; border-bottom: 1px solid #30363d; }
    .video-body { padding: 5px; }
    .stat-card { background: #1c2128; padding: 15px; border-radius: 12px; border: 1px solid #30363d; text-align: center; margin-bottom: 10px; }
    .success-card { background: #0d1117; padding: 12px; border-radius: 8px; border-left: 4px solid #238636; margin-bottom: 8px; border: 1px solid #30363d; }
    div[data-testid="stNumberInput"] button { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

all_db = load_all_data()

for col in ['tamamlandi', 'id', 'soru_cozulen', 'soru_hedef']:
    if col in all_db.columns:
        if col == 'tamamlandi':
            all_db[col] = all_db[col].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, '1.0': True, '0.0': False}).fillna(False)
        else:
            all_db[col] = pd.to_numeric(all_db[col], errors='coerce').fillna(0).astype(int)

# --- 4. GİRİŞ ---
if st.session_state.user is None:
    st.markdown('<div class="custom-header"><h1>🚀 2026 KPSS Çalışma Planı Giriş</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t1:
        with st.form("login_form"):
            u, p = st.text_input("Kullanıcı Adı"), st.text_input("Şifre", type="password")
            if st.form_submit_button("Sisteme Bağlan", use_container_width=True):
                if not all_db.empty and u in all_db['username'].values:
                    if all_db[all_db['username'] == u]['password'].iloc[0] == hash_password(p):
                        st.session_state.user = u; st.rerun()
                st.error("Hatalı giriş!")
    with t2:
        with st.form("reg_form"):
            nu, np = st.text_input("Yeni Kullanıcı"), st.text_input("Yeni Şifre", type="password")
            if st.form_submit_button("Hesap Oluştur", use_container_width=True):
                if nu in all_db['username'].values: st.error("Mevcut kullanıcı.")
                else:
                    new_u = pd.DataFrame([{"username": nu, "password": hash_password(np), "tamamlandi": True, "id": 0, "konu": "Hesap Aktif"}])
                    save_to_gsheets(pd.concat([all_db, new_u], ignore_index=True))
                    st.success("Kayıt başarılı!")
    st.stop()

# --- 5. ANA EKRAN ---
username = st.session_state.user
user_df = all_db[all_db['username'] == username].copy()
st.sidebar.markdown(f"👤 **{username}**")
if st.sidebar.button("🚪 Çıkış"): st.session_state.user = None; st.rerun()

menu = st.sidebar.radio("Gezinti", ["📅 Günlük Planım", "📝 Plan Oluştur", "🏆 Başarılarım"])
st.markdown('<div class="custom-header"><h1>🚀 <span style="color: #58a6ff;">2026 KPSS</span> ÇALIŞMA PLANI</h1></div>', unsafe_allow_html=True)

# --- 6. PLAN OLUŞTUR ---
if menu == "📝 Plan Oluştur":
    st.subheader("📝 Yeni Çalışma Planı")
    with st.expander("➕ Yeni Ders Ekle"):
        c_add1, c_add2, c_add3 = st.columns([5, 1, 1.5])
        with c_add1: n_d = st.text_input("Ders Adı", key="new_lesson_input")
        with c_add2:
            with st.popover(st.session_state.selected_icon):
                emos = ["📚", "📐", "🏛️", "🌍", "📰", "⚖️", "🧪", "🎨", "💻", "🔥", "📌"]
                cols = st.columns(4)
                for i, emo in enumerate(emos):
                    if cols[i%4].button(emo, key=f"emo_{i}"): st.session_state.selected_icon = emo; st.rerun()
        with c_add3:
            if st.button("Ekle", type="primary") and n_d:
                st.session_state.dersler[n_d] = st.session_state.selected_icon; st.rerun()
    
    st.divider()
    # Form yapısı inputları sıfırlamak için en sağlıklı yoldur
    with st.form("plan_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d_s = c1.selectbox("Ders", list(st.session_state.dersler.keys()))
        k_a = c1.text_input("Konu")
        t_r = c2.date_input("Tarih")
        s_h = c2.number_input("Hedef Soru", min_value=1, value=50)
        v_s = st.select_slider("Video Sayısı", options=range(1, 11), value=1)
        v_u = [st.text_input(f"Video {i+1} Linki", key=f"link_{i}") for i in range(v_s)]
        
        if st.form_submit_button("🚀 PLANI KAYDET", use_container_width=True):
            if k_a:
                v_d = json.dumps([{"url": format_yt_link(u), "done": False} for u in v_u if u.strip()])
                n_p = pd.DataFrame([{"username": username, "password": user_df['password'].iloc[0], "ders": d_s, "konu": k_a, "tarih": str(t_r), "videolar": v_d, "soru_hedef": s_h, "soru_cozulen": 0, "tamamlandi": False, "id": int(datetime.now().timestamp())}])
                save_to_gsheets(pd.concat([all_db, n_p], ignore_index=True))
                # GERİ BİLDİRİM (POP-UP TARZI)
                st.toast(f"✅ {k_a} planı başarıyla eklendi!", icon='🚀')
                st.success("Plan başarıyla kaydedildi! Sayfa temizleniyor...")
                time.sleep(1)
                st.rerun()
            else: st.warning("Lütfen konu adını girin!")

# --- 7. GÜNLÜK PLANIM ---
elif menu == "📅 Günlük Planım":
    col_t, col_tog = st.columns([4, 1.2])
    with col_t: st.subheader("🎯 Bugünkü Görevlerin")
    with col_tog: show_history = st.toggle("✅ Tamamlananlar") 

    active_df = user_df[(user_df['tamamlandi'] == show_history) & (user_df['konu'] != "Hesap Aktif")]
    if active_df.empty: st.info("Burada henüz bir şey yok.")
    else:
        for idx, row in active_df.iterrows():
            ikon = st.session_state.dersler.get(row['ders'], "📌")
            with st.expander(f"{ikon} {row['ders']} - {row['konu']}", expanded=not show_history):
                v_l = json.loads(row['videolar']) if isinstance(row['videolar'], str) else []
                cl, cr = st.columns([4, 1.5])
                with cl:
                    if v_l:
                        v_cols = st.columns(3 if len(v_l) > 1 else 1)
                        for v_i, v in enumerate(v_l):
                            with v_cols[v_i % len(v_cols)]:
                                if not v['done']:
                                    st.markdown(f'<div class="video-container"><div class="video-label-bar">{v_i+1}. Video</div><div class="video-body">', unsafe_allow_html=True)
                                    st.video(v['url']); st.markdown('</div></div>', unsafe_allow_html=True)
                                    if st.button(f"İzlendi ✅", key=f"v_{row['id']}_{v_i}"):
                                        v['done'] = True; all_db.loc[all_db['id'] == row['id'], 'videolar'] = json.dumps(v_l)
                                        save_to_gsheets(all_db); st.rerun()
                                else: st.success(f"✅ {v_i+1}. Bitti")
                with cr:
                    st.write(f"**Hedef:** {row['soru_hedef']}")
                    n_q = st.number_input("Çözülen", value=int(row['soru_cozulen']), key=f"q_{row['id']}")
                    if n_q != row['soru_cozulen']:
                        all_db.loc[all_db['id'] == row['id'], 'soru_cozulen'] = n_q; save_to_gsheets(all_db); st.rerun()
                    st.progress(min(int(n_q)/int(row['soru_hedef']), 1.0) if row['soru_hedef']>0 else 0)
                    if not show_history:
                        if st.button("🌟 TAMAMLA", key=f"f_{row['id']}", type="primary", use_container_width=True):
                            all_db.loc[all_db['id'] == row['id'], 'tamamlandi'] = True
                            save_to_gsheets(all_db)
                            # TAMAMLAMA GERİ BİLDİRİMİ
                            st.toast(f"Tebrikler! {row['konu']} konusunu bitirdin!", icon='🏆')
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                    if st.button("🗑️ Sil", key=f"d_{row['id']}", use_container_width=True):
                        save_to_gsheets(all_db[all_db['id'] != row['id']]); st.rerun()

# --- 8. BAŞARILARIM ---
elif menu == "🏆 Başarılarım":
    bitenler = user_df[user_df['tamamlandi'] & (user_df['konu'] != "Hesap Aktif")]
    st.markdown("### 📊 Genel Başarı Tablon")
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="stat-card"><h2>🔥 {int(bitenler["soru_cozulen"].sum())}</h2>Soru Çözüldü</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><h2>✅ {len(bitenler)}</h2>Konu Tamamlandı</div>', unsafe_allow_html=True)
