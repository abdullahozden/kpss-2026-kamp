import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import hashlib
from collections import defaultdict
from datetime import datetime

# --- 1. BAĞLANTI VE YARDIMCI FONKSİYONLAR ---
conn = st.connection("gsheets", type=GSheetsConnection)

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def load_all_data():
    try:
        # Sheet'teki tüm verileri çek
        df = conn.read(ttl=0)
        return df.dropna(how="all")
    except Exception as e:
        # Tablo tamamen boşsa başlıkları içeren boş bir DF oluştur
        return pd.DataFrame(columns=["username", "password", "ders", "konu", "tarih", "videolar", "soru_hedef", "soru_cozulen", "tamamlandi", "id"])

def save_to_gsheets(df):
    try:
        conn.update(data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Veri kaydedilemedi: {e}")
        return False

def format_yt_link(url):
    url = url.strip()
    return url if url.startswith("http") else f"https://{url}" if url else ""

# --- 2. AYARLAR VE TASARIM ---
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
    .stPopover button { height: 42px !important; min-width: 50px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GİRİŞ VE KAYIT SİSTEMİ ---
all_db = load_all_data()

if st.session_state.user is None:
    st.markdown('<div class="custom-header" style="text-align:center;"><h1>🚀 2026 KPSS Kampı Giriş</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with tab1:
        with st.form("login_form"):
            u_name = st.text_input("Kullanıcı Adı")
            u_pass = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş", use_container_width=True):
                # Kullanıcı kontrolü (username ve şifre hash'i eşleşmeli)
                user_check = all_db[(all_db['username'] == u_name) & (all_db['password'] == hash_password(u_pass))]
                if not user_check.empty:
                    st.session_state.user = u_name
                    st.success("Giriş başarılı!")
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")
    
    with tab2:
        with st.form("register_form"):
            new_name = st.text_input("Kullanıcı Adı")
            new_pass = st.text_input("Şifre", type="password")
            confirm_pass = st.text_input("Şifre Tekrar", type="password")
            if st.form_submit_button("Kayıt Ol", use_container_width=True):
                if new_name in all_db['username'].values:
                    st.error("Bu kullanıcı adı zaten alınmış.")
                elif new_pass != confirm_pass:
                    st.error("Şifreler uyuşmuyor.")
                elif len(new_pass) < 4:
                    st.error("Şifre en az 4 karakter olmalı.")
                else:
                    # Yeni kullanıcıyı boş bir plan satırıyla veya sadece hesap bilgisiyle ekle
                    reg_row = pd.DataFrame([{
                        "username": new_name, "password": hash_password(new_pass),
                        "ders": "Sistem", "konu": "Hesap Oluşturuldu", "tarih": str(datetime.now().date()),
                        "videolar": "[]", "soru_hedef": 0, "soru_cozulen": 0, "tamamlandi": True, "id": int(datetime.now().timestamp())
                    }])
                    updated_db = pd.concat([all_db, reg_row], ignore_index=True)
                    if save_to_gsheets(updated_db):
                        st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
    st.stop()

# --- 4. ANA UYGULAMA ---
username = st.session_state.user
user_df = all_db[all_db['username'] == username].copy()

st.sidebar.markdown(f"👤 Hoş geldin, **{username}**")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.user = None
    st.rerun()

menu = st.sidebar.radio("Menü", ["📅 Günlük Planım", "📝 Plan Oluştur", "🏆 Başarılarım"])

# --- 5. PLAN OLUŞTUR ---
if menu == "📝 Plan Oluştur":
    st.subheader("📝 Yeni Plan")
    with st.expander("➕ Yeni Ders Ekle"):
        c_add1, c_add2, c_add3 = st.columns([5, 1, 1.5])
        with c_add1:
            d_name = st.text_input("Ders Adı", placeholder="Örn: Vatandaşlık", label_visibility="collapsed")
        with c_add2:
            with st.popover(st.session_state.selected_icon, use_container_width=True):
                emojiler = ["📚", "📐", "🏛️", "🌍", "📰", "⚖️", "🧪", "🎨", "💻", "⏰", "💡", "🔥"]
                cols = st.columns(4)
                for i, emo in enumerate(emojiler):
                    if cols[i % 4].button(emo, key=f"emo_{i}"):
                        st.session_state.selected_icon = emo
                        st.rerun()
        with c_add3:
            if st.button("Ekle", use_container_width=True, type="primary"):
                if d_name:
                    st.session_state.dersler[d_name] = st.session_state.selected_icon
                    st.rerun()

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        d_secim = st.selectbox("Ders Seç", list(st.session_state.dersler.keys()))
        k_adi = st.text_input("Konu Adı")
    with c2:
        tarih = st.date_input("Tarih", format="DD/MM/YYYY")
        s_hedef = st.number_input("Soru Hedefi", min_value=1, value=50)

    v_sayisi = st.select_slider("Video Sayısı", options=range(1, 6), value=1)
    with st.form("plan_form"):
        v_urls = [st.text_input(f"Video {i+1} URL", key=f"url_{i}") for i in range(v_sayisi)]
        if st.form_submit_button("Google Sheets'e Kaydet", use_container_width=True):
            if k_adi:
                v_data = json.dumps([{"url": format_yt_link(u), "done": False} for u in v_urls if u.strip()])
                new_row = pd.DataFrame([{
                    "username": username, "password": all_db[all_db['username'] == username]['password'].values[0],
                    "ders": d_secim, "konu": k_adi, "tarih": str(tarih),
                    "videolar": v_data, "soru_hedef": int(s_hedef), "soru_cozulen": 0,
                    "tamamlandi": False, "id": int(datetime.now().timestamp())
                }])
                updated_db = pd.concat([all_db, new_row], ignore_index=True)
                if save_to_gsheets(updated_db):
                    st.success("Plan kaydedildi!")
                    st.rerun()

# --- 6. GÜNLÜK PLANIM ---
elif menu == "📅 Günlük Planım":
    col_t, col_tog = st.columns([4, 1])
    with col_t: st.subheader("📅 Görev Takibi")
    with col_tog: show_history = st.toggle("📜 Arşiv")

    # Veriyi listelerken tip güvenliğini sağla
    user_df['tamamlandi'] = user_df['tamamlandi'].astype(bool)
    display_df = user_df[user_df['tamamlandi'] == show_history]
    
    if display_df.empty:
        st.info("Gösterilecek bir kayıt bulunamadı.")
    else:
        for idx_row, row in display_df.iterrows():
            # Index'i all_db üzerinden bulmak için 'id' kullanıyoruz
            db_idx = all_db[all_db['id'] == row['id']].index[0]
            
            ikon = st.session_state.dersler.get(row['ders'], "📌")
            with st.expander(f"{ikon} {row['ders']} - {row['konu']}"):
                try:
                    v_list = json.loads(row['videolar'])
                except:
                    v_list = []
                
                c_v, c_s = st.columns([3, 1])
                with c_v:
                    for v_idx, v in enumerate(v_list):
                        if not v.get('done', False):
                            st.video(v['url'])
                            if st.button(f"İzlendi ✅", key=f"v_{row['id']}_{v_idx}"):
                                v['done'] = True
                                all_db.at[db_idx, 'videolar'] = json.dumps(v_list)
                                save_to_gsheets(all_db); st.rerun()
                        else: st.info(f"📹 Video {v_idx+1} tamamlandı.")
                
                with c_s:
                    current_q = int(row['soru_cozulen'])
                    new_q = st.number_input("Soru", value=current_q, key=f"q_{row['id']}")
                    if new_q != current_q:
                        all_db.at[db_idx, 'soru_cozulen'] = int(new_q)
                        save_to_gsheets(all_db); st.rerun()
                    
                    if st.button("🌟 BİTİR" if not show_history else "⏪ GERİ AL", key=f"f_{row['id']}", use_container_width=True):
                        all_db.at[db_idx, 'tamamlandi'] = not show_history
                        save_to_gsheets(all_db); st.rerun()
                    
                    if st.button("🗑️ Sil", key=f"d_{row['id']}", use_container_width=True):
                        all_db = all_db.drop(db_idx)
                        save_to_gsheets(all_db); st.rerun()

# --- 7. BAŞARILARIM ---
elif menu == "🏆 Başarılarım":
    user_df['soru_cozulen'] = pd.to_numeric(user_df['soru_cozulen'], errors='coerce').fillna(0)
    bitenler = user_df[user_df['tamamlandi'] == True]
    st.metric("Toplam Çözülen Soru", int(sum(bitenler['soru_cozulen'])))
    st.dataframe(bitenler[['ders', 'konu', 'soru_cozulen', 'tarih']], use_container_width=True)
