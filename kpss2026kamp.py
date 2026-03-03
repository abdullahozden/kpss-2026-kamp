import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import hashlib
from datetime import datetime

# --- 1. CONFIG & CACHE ---
st.set_page_config(page_title="2026 KPSS Çalışma Planı", layout="wide", page_icon="🎓")

# Veri çekme işlemini optimize et (Sadece veri değiştiğinde veya 10 dakikada bir yenilenir)
@st.cache_data(ttl=600)
def load_data(_conn):
    try:
        df = _conn.read(ttl=0)
        return df.dropna(how="all") if df is not None else pd.DataFrame()
    except:
        return pd.DataFrame()

def save_data(conn, df):
    conn.update(data=df)
    st.cache_data.clear() # Kayıt sonrası önbelleği temizle

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. THEME & CSS (Minimalist & High Performance) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    [data-testid="stSidebarNav"] span { font-size: 1.1rem !important; font-weight: 600; }
    .custom-header {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 1.5rem; border-radius: 15px; border-bottom: 3px solid #3b82f6;
        margin-bottom: 2rem; text-align: center;
    }
    .video-container { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 10px; overflow: hidden; }
    .video-label-bar { background-color: #1c2128; color: #58a6ff; padding: 4px; font-size: 0.8rem; font-weight: 700; text-align: center; border-bottom: 1px solid #30363d; }
    .video-body { padding: 5px; }
    .stat-card { background: #1c2128; padding: 10px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .success-card { background: #0d1117; padding: 10px; border-radius: 8px; border-left: 4px solid #238636; border: 1px solid #30363d; margin-bottom: 5px; }
    div[data-testid="stNumberInput"] button { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION & CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)
if 'user' not in st.session_state: st.session_state.user = None
if 'selected_icon' not in st.session_state: st.session_state.selected_icon = "📌"
if 'dersler' not in st.session_state:
    st.session_state.dersler = {"Matematik": "📐", "Türkçe": "📚", "Tarih": "🏛️", "Coğrafya": "🌍", "Güncel Bilgiler": "📰"}

# Veriyi bir kez çek
all_db = load_data(conn)

# Tip dönüşümlerini sadece veri varsa ve bir kez yap (Optimizasyon)
if not all_db.empty:
    for col in ['tamamlandi', 'id', 'soru_cozulen', 'soru_hedef']:
        if col in all_db.columns:
            if col == 'tamamlandi':
                all_db[col] = all_db[col].astype(str).str.lower().isin(['true', '1', '1.0'])
            else:
                all_db[col] = pd.to_numeric(all_db[col], errors='coerce').fillna(0).astype(int)

# --- 4. AUTHENTICATION ---
if st.session_state.user is None:
    st.markdown('<div class="custom-header"><h1>🚀 2026 KPSS Planlayıcı</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş", "📝 Kayıt"])
    with t1:
        with st.form("l_f"):
            u, p = st.text_input("Kullanıcı"), st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş", use_container_width=True):
                if not all_db.empty and u in all_db['username'].values:
                    if all_db[all_db['username'] == u]['password'].iloc[0] == hash_password(p):
                        st.session_state.user = u; st.rerun()
                st.error("Hatalı kullanıcı veya şifre!")
    with t2:
        with st.form("r_f"):
            nu, np = st.text_input("Yeni Kullanıcı"), st.text_input("Yeni Şifre", type="password")
            if st.form_submit_button("Kayıt Ol", use_container_width=True):
                if not all_db.empty and nu in all_db['username'].values: st.error("Mevcut kullanıcı!")
                else:
                    new_row = pd.DataFrame([{"username": nu, "password": hash_password(np), "tamamlandi": True, "id": 0, "konu": "Hesap Aktif"}])
                    save_data(conn, pd.concat([all_db, new_row], ignore_index=True))
                    st.success("Kayıt başarılı!"); st.rerun()
    st.stop()

# --- 5. APP MAIN ---
user_df = all_db[all_db['username'] == st.session_state.user].copy()
st.sidebar.subheader(f"👤 {st.session_state.user}")
if st.sidebar.button("🚪 Çıkış"): st.session_state.user = None; st.rerun()

menu = st.sidebar.radio("Menü", ["📅 Ders Çalışma Planım", "📝 Plan Oluştur", "🏆 Başarılarım"])
st.markdown(f'<div class="custom-header"><h1>🚀 <span style="color: #58a6ff;">2026 KPSS</span> PLANI</h1></div>', unsafe_allow_html=True)

# --- PLAN OLUŞTUR ---
if menu == "📝 Plan Oluştur":
    with st.expander("➕ Yeni Ders Tanımla"):
        c1, c2, c3 = st.columns([4, 1, 1])
        nd = c1.text_input("Ders Adı")
        with c2: 
            with st.popover(st.session_state.selected_icon):
                emos = ["📚", "📐", "🏛️", "🌍", "📰", "⚖️", "🧪", "🎨", "💻", "🔥"]
                cols = st.columns(5)
                for i, emo in enumerate(emos):
                    if cols[i%5].button(emo, key=f"e_{i}"): st.session_state.selected_icon = emo; st.rerun()
        if c3.button("Ekle") and nd: st.session_state.dersler[nd] = st.session_state.selected_icon; st.rerun()

    with st.form("p_f"):
        col1, col2 = st.columns(2)
        ds = col1.selectbox("Ders", list(st.session_state.dersler.keys()))
        ka = col1.text_input("Konu")
        tr = col2.date_input("Tarih")
        sh = col2.number_input("Hedef Soru", min_value=1, value=100)
        vs = st.slider("Video Sayısı", 1, 10, 1)
        v_links = [st.text_input(f"Video {i+1} Linki", key=f"v_{i}") for i in range(vs)]
        if st.form_submit_button("Planı Oluştur", use_container_width=True) and ka:
            v_json = json.dumps([{"url": l.strip(), "done": False} for l in v_links if l.strip()])
            new_p = pd.DataFrame([{"username": st.session_state.user, "password": user_df['password'].iloc[0], "ders": ds, "konu": ka, "tarih": str(tr), "videolar": v_json, "soru_hedef": sh, "soru_cozulen": 0, "tamamlandi": False, "id": int(datetime.now().timestamp())}])
            save_data(conn, pd.concat([all_db, new_p], ignore_index=True))
            st.success("Plan eklendi!"); st.rerun()

# --- GÜNLÜK PLAN ---
elif menu == "📅 Ders Çalışma Planım":
    show_h = st.toggle("✅ Tamamlananları Göster")
    display_df = user_df[(user_df['tamamlandi'] == show_h) & (user_df['konu'] != "Hesap Aktif")]
    
    if display_df.empty: st.info("Gösterilecek görev bulunamadı.")
    else:
        for idx, row in display_df.iterrows():
            with st.expander(f"{st.session_state.dersler.get(row['ders'], '📌')} {row['ders']} - {row['konu']}", expanded=not show_h):
                c_v, c_s = st.columns([4, 1.5])
                v_list = json.loads(row['videolar']) if isinstance(row['videolar'], str) else []
                with c_v:
                    if v_list:
                        v_cols = st.columns(3 if len(v_list) > 1 else 1)
                        for i, v in enumerate(v_list):
                            with v_cols[i % len(v_cols)]:
                                if not v['done']:
                                    st.markdown(f'<div class="video-container"><div class="video-label-bar">{i+1}. Video</div><div class="video-body">', unsafe_allow_html=True)
                                    st.video(v['url'])
                                    st.markdown('</div></div>', unsafe_allow_html=True)
                                    if st.button("İzlendi ✅", key=f"v_{row['id']}_{i}"):
                                        v['done'] = True; all_db.loc[all_db['id'] == row['id'], 'videolar'] = json.dumps(v_list)
                                        save_data(conn, all_db); st.rerun()
                                else: st.caption(f"✅ {i+1}. Video bitti")
                with c_s:
                    st.write(f"**Hedef:** {row['soru_hedef']}")
                    cq = st.number_input("Çözülen", value=int(row['soru_cozulen']), key=f"q_{row['id']}")
                    if cq != row['soru_cozulen']:
                        all_db.loc[all_db['id'] == row['id'], 'soru_cozulen'] = cq; save_data(conn, all_db); st.rerun()
                    prog = min(int(cq)/int(row['soru_hedef']), 1.0) if row['soru_hedef'] > 0 else 0
                    st.progress(prog)
                    if not show_h:
                        if st.button("🌟 TAMAMLA", key=f"f_{row['id']}", type="primary", use_container_width=True):
                            all_db.loc[all_db['id'] == row['id'], 'tamamlandi'] = True; save_data(conn, all_db); st.balloons(); st.rerun()
                    if st.button("🗑️ Sil", key=f"d_{row['id']}", use_container_width=True):
                        save_data(conn, all_db[all_db['id'] != row['id']]); st.rerun()

# --- BAŞARILAR ---
elif menu == "🏆 Başarılarım":
    done = user_df[user_df['tamamlandi'] & (user_df['konu'] != "Hesap Aktif")]
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="stat-card"><h2>🔥 {int(done["soru_cozulen"].sum())}</h2>Soru</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><h2>✅ {len(done)}</h2>Konu</div>', unsafe_allow_html=True)
    
    for d, ikon in st.session_state.dersler.items():
        d_df = user_df[user_df['ders'] == d]
        if not d_df.empty:
            b_df = d_df[d_df['tamamlandi']]
            perc = int(len(b_df)/len(d_df)*100) if not d_df.empty else 0
            st.write(f"### {ikon} {d} (%{perc})")
            st.progress(perc/100)
            with st.expander("Detaylar"):
                for _, b in b_df.iterrows():
                    st.markdown(f'<div class="success-card"><b>{b["konu"]}</b> - {int(b["soru_cozulen"])} Soru</div>', unsafe_allow_html=True)


