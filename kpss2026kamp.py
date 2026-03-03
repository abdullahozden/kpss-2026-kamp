import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import hashlib
from collections import defaultdict
from datetime import datetime

# --- 1. BAĞLANTI VE GÜVENLİK ---
# Google Sheets bağlantısını başlatıyoruz
conn = st.connection("gsheets", type=GSheetsConnection)

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Kullanıcı verilerini Sheets'ten çekme
def load_all_data():
    try:
        # ttl=0 her seferinde güncel veriyi çeker (cache'lemez)
        return conn.read(ttl=0).dropna(how="all")
    except:
        # Eğer tablo boşsa veya hata verirse boş bir DataFrame döner
        return pd.DataFrame(columns=["username", "ders", "konu", "tarih", "videolar", "soru_hedef", "soru_cozulen", "tamamlandi", "id"])

# Verileri Sheets'e kaydetme
def save_to_gsheets(df):
    conn.update(data=df)
    st.cache_data.clear()

def format_yt_link(url):
    url = url.strip()
    return url if url.startswith("http") else f"https://{url}" if url else ""

# --- 2. TASARIM VE OTURUM AYARLARI ---
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
        max-height: 400px; overflow-y: auto; padding: 15px;
        background: #0d1117; border-radius: 12px; border: 1px solid #30363D;
    }
    .history-item {
        background: #161b22; padding: 10px; border-radius: 8px; 
        margin-bottom: 5px; border: 1px solid #30363d;
    }
    .stPopover button { height: 42px !important; min-width: 50px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GİRİŞ VE KAYIT SİSTEMİ (Sheets üzerinden) ---
# Not: Gerçek bir projede şifreler ayrı bir Sheet'te tutulmalıdır. 
# Basitlik için burada tek tablo mantığıyla ilerliyoruz veya ayrı bir 'Users' tablosu açabilirsin.

all_db = load_all_data()

if st.session_state.user is None:
    st.markdown('<div class="custom-header" style="text-align:center;"><h1>🚀 2026 KPSS Kampı Giriş</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with tab1:
        with st.form("login"):
            u_name = st.text_input("Kullanıcı Adı")
            u_pass = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş", use_container_width=True):
                # Örnek: 'admin' kullanıcısı ve şifresi sistemde kayıtlı mı kontrolü
                # (Bu kısım için 'users' isimli ikinci bir Sheet sayfası oluşturmak en sağlıklısıdır)
                # Şimdilik direkt giriş yapalım, Sheets entegrasyonu plan kısmında odaklanalım:
                st.session_state.user = u_name
                st.rerun()
    
    with tab2:
        st.info("Kayıt olduktan sonra giriş yapabilirsiniz. (Şu an deneme modundadır)")
    st.stop()

# --- 4. ANA UYGULAMA ---
username = st.session_state.user
# Sadece mevcut kullanıcıya ait verileri filtrele
user_df = all_db[all_db['username'] == username].copy()

st.sidebar.markdown(f"👤 Hoş geldin, **{username}**")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.user = None
    st.rerun()

menu = st.sidebar.radio("Menü", ["📅 Günlük Planım", "📝 Plan Oluştur", "🏆 Başarılarım"])

# --- 5. PLAN OLUŞTUR (Sheets'e Kaydetme) ---
if menu == "📝 Plan Oluştur":
    st.subheader("📝 Yeni Plan")
    with st.expander("➕ Yeni Ders Ekle", expanded=True):
        c_add1, c_add2, c_add3 = st.columns([5, 1, 1.5])
        with c_add1:
            new_name = st.text_input("Ders Adı", placeholder="Örn: Geometri", label_visibility="collapsed")
        with c_add2:
            with st.popover(st.session_state.selected_icon, use_container_width=True):
                emojiler = ["📚", "📐", "🏛️", "🌍", "📰", "⚖️", "🧪", "🎨", "💻", "⏰", "💡", "🔥"]
                cols = st.columns(4)
                for i, emo in enumerate(emojiler):
                    if cols[i % 4].button(emo, key=f"e_{i}"):
                        st.session_state.selected_icon = emo
                        st.rerun()
        with c_add3:
            if st.button("Ekle", use_container_width=True, type="primary"):
                st.session_state.dersler[new_name] = st.session_state.selected_icon
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
    with st.form("plan_kaydet"):
        v_urls = [st.text_input(f"Video {i+1} URL", key=f"vurl_{i}") for i in range(v_sayisi)]
        if st.form_submit_button("Planı Sheets'e Kaydet", use_container_width=True):
            if k_adi:
                # Video listesini JSON string olarak saklayacağız (Sheet hücre kısıtlaması nedeniyle)
                v_data = json.dumps([{"url": format_yt_link(u), "done": False} for u in v_urls if u.strip()])
                
                new_row = pd.DataFrame([{
                    "username": username, "ders": d_secim, "konu": k_adi,
                    "tarih": str(tarih), "videolar": v_data, "soru_hedef": s_hedef,
                    "soru_cozulen": 0, "tamamlandi": False, "id": int(datetime.now().timestamp())
                }])
                
                updated_db = pd.concat([all_db, new_row], ignore_index=True)
                save_to_gsheets(updated_db)
                st.success("Veriler Google Sheets'e gönderildi!")
                st.rerun()

# --- 6. GÜNLÜK PLANIM ---
elif menu == "📅 Günlük Planım":
    col_t, col_tog = st.columns([4, 1])
    with col_t: st.subheader("📅 Görev Takibi")
    with col_tog: show_history = st.toggle("Arşiv")

    # Filtreleme: Tamamlanan / Aktif
    display_df = user_df[user_df['tamamlandi'] == show_history]
    
    if display_df.empty:
        st.info("Burada henüz bir şey yok.")
    else:
        for index, row in display_df.iterrows():
            ikon = st.session_state.dersler.get(row['ders'], "📌")
            with st.expander(f"{ikon} {row['ders']} - {row['konu']}"):
                # Video işlemleri (JSON string'den geri çevirme)
                v_list = json.loads(row['videolar']) if isinstance(row['videolar'], str) else []
                
                c_v, c_s = st.columns([3, 1])
                with c_v:
                    if v_list:
                        for v_idx, v in enumerate(v_list):
                            if not v['done']:
                                st.video(v['url'])
                                if st.button(f"Video {v_idx+1} Bitti", key=f"vbtn_{row['id']}_{v_idx}"):
                                    v['done'] = True
                                    all_db.at[index, 'videolar'] = json.dumps(v_list)
                                    save_to_gsheets(all_db); st.rerun()
                            else: st.write(f"✅ Video {v_idx+1} İzlendi")
                
                with c_s:
                    new_q = st.number_input("Soru", value=int(row['soru_cozulen']), key=f"q_{row['id']}")
                    if new_q != row['soru_cozulen']:
                        all_db.at[index, 'soru_cozulen'] = new_q
                        save_to_gsheets(all_db); st.rerun()
                    
                    if st.button("🌟 BİTİR" if not show_history else "⏪ GERİ AL", key=f"fin_{row['id']}", use_container_width=True):
                        all_db.at[index, 'tamamlandi'] = not show_history
                        save_to_gsheets(all_db); st.rerun()
                    
                    if st.button("🗑️ Sil", key=f"del_{row['id']}", use_container_width=True):
                        all_db = all_db.drop(index)
                        save_to_gsheets(all_db); st.rerun()

# --- 7. BAŞARILARIM ---
elif menu == "🏆 Başarılarım":
    bitenler = user_df[user_df['tamamlandi'] == True]
    st.metric("Toplam Çözülen Soru", sum(bitenler['soru_cozulen'].astype(int)))
    st.dataframe(bitenler[['ders', 'konu', 'soru_cozulen', 'tarih']], use_container_width=True)
