import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import hashlib
from datetime import datetime
import time

# --- 1. VERİ BAĞLANTISI & OPTİMİZASYON ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Veri çekme işlemini cache ile hızlandırıyoruz (Sunucu yükünü azaltır)
@st.cache_data(ttl=300)
def load_all_data():
    try:
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["username", "password", "ders", "konu", "tarih", "videolar", "soru_hedef", "soru_cozulen", "tamamlandi", "id"])
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=["username", "password", "ders", "konu", "tarih", "videolar", "soru_hedef", "soru_cozulen", "tamamlandi", "id"])

def save_to_gsheets(df):
    conn.update(data=df)
    st.cache_data.clear() # Değişiklik olduğunda cache'i temizle

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def format_yt_link(url):
    url = url.strip()
    return url if url.startswith("http") else f"https://{url}" if url else ""
def delete_user_account(df, username):
    new_df = df[df['username'] != username]
    save_to_gsheets(new_df)
    st.cache_data.clear()

# --- 2. TASARIM AYARLARI (ESKİ TASARIM BİREBİR KORUNDU) ---
st.set_page_config(page_title="2026 KPSS ÇALIŞMA PLANI", layout="wide", page_icon="🎓")

if 'user' not in st.session_state: st.session_state.user = None
if 'selected_icon' not in st.session_state: st.session_state.selected_icon = "📌"
if 'dersler' not in st.session_state:
    st.session_state.dersler = {"Matematik": "📐", "Türkçe": "📚", "Tarih": "🏛️", "Coğrafya": "🌍", "Güncel Bilgiler": "📰"}

st.markdown("""
    <style>
    /* Ana Arka Plan */
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    
    /* Yan Menü (Sidebar) Büyütme */
    [data-testid="stSidebarNav"] span { font-size: 1.2rem !important; font-weight: 600 !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { font-size: 1.1rem !important; padding: 10px 0 !important; }
    
    /* Modern Header */
    .custom-header {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 2rem; border-radius: 20px; border-bottom: 4px solid #3b82f6;
        margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: center;
    }
    
    /* Plan Kartları */
    .stExpander { background-color: #161b22 !important; border: 1px solid #30363d !important; border-radius: 12px !important; margin-bottom: 1rem !important; }
    
    /* Geliştirilmiş Video Kutusu (Tam Olarak İstediğin Yapı) */
    .video-container {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        margin-bottom: 10px;
        overflow: hidden;
    }

    /* İşaretlediğin kutucuğun stili */
    .video-label-bar {
        background-color: #1c2128; 
        color: #58a6ff; 
        padding: 4px 8px;
        font-size: 0.85rem;
        font-weight: 700;
        text-align: center;
        border-bottom: 1px solid #30363d;
        letter-spacing: 0.5px;
    }

    .video-body {
        padding: 5px;
    }
    
    /* Tamamlananlar (Arşiv) Satırı */
    .history-item {
        background: rgba(56, 139, 253, 0.1);
        padding: 12px 20px; border-radius: 12px; 
        border: 1px solid rgba(56, 139, 253, 0.2);
        display: flex; align-items: center; justify-content: align-items;
    }

    .stat-card { background: #1c2128; padding: 15px; border-radius: 12px; border: 1px solid #30363d; text-align: center; margin-bottom: 10px; }
    .success-card { background: #0d1117; padding: 12px; border-radius: 8px; border-left: 4px solid #238636; margin-bottom: 8px; border: 1px solid #30363d; }
    div[data-testid="stNumberInput"] button { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERİ ÇEKME VE TİP DÖNÜŞÜMÜ ---
all_db = load_all_data()

for col in ['tamamlandi', 'id', 'soru_cozulen', 'soru_hedef']:
    if col in all_db.columns:
        if col == 'tamamlandi':
            all_db[col] = all_db[col].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, '1.0': True, '0.0': False}).fillna(False)
        else:
            all_db[col] = pd.to_numeric(all_db[col], errors='coerce').fillna(0 if col != 'soru_hedef' else 1).astype(int)

# --- 4. GİRİŞ KONTROLÜ ---
if st.session_state.user is None:
    st.markdown('<div class="custom-header"><h1>🚀 2026 KPSS Çalışma Planı Giriş</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t1:
        with st.form("login_form"):
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.form_submit_button("Sisteme Bağlan", use_container_width=True):
                user_check = all_db[(all_db['username'] == u) & (all_db['password'] == hash_password(p))]
                if not user_check.empty:
                    st.session_state.user = u; st.rerun()
                else: st.error("Hatalı giriş!")
    with t2:
        with st.form("reg_form"):
            nu = st.text_input("Yeni Kullanıcı Adı")
            np = st.text_input("Yeni Şifre", type="password")
            if st.form_submit_button("Hesap Oluştur", use_container_width=True):
                if nu in all_db['username'].values: st.error("Bu kullanıcı mevcut.")
                else:
                    new_u_row = pd.DataFrame([{"username": nu, "password": hash_password(np), "tamamlandi": True, "id": 0, "konu": "Hesap Aktif", "soru_cozulen": 0, "soru_hedef": 1}])
                    save_to_gsheets(pd.concat([all_db, new_u_row], ignore_index=True))
                    st.success("Kayıt başarılı!")
    st.stop()

# --- 5. ANA EKRAN ---
username = st.session_state.user
user_df = all_db[all_db['username'] == username].copy()

st.sidebar.markdown(f"👤 **{username}**")
if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
    st.session_state.user = None
    st.rerun()
st.markdown("<hr style='margin:1px 0px;'>", unsafe_allow_html=True)
with st.sidebar.expander("⚙️ Hesap Ayarları"):
    st.subheader("Görünüm")
    tema = st.radio("Tema Seçimi", ["Karanlık", "Aydınlık"], index=0 if st.session_state.get('theme') == 'dark' else 1)
    if tema == "Aydınlık":
        st.markdown("""
            <style>
            /* 1. Sayfa Temeli - Göz yormayan açık gri */
            .stApp {
                background-color: #F7F9FC !important;
                color: #2D3436 !important;
            }

            /* 2. Sidebar - Net bir ayırım için biraz daha koyu */
            [data-testid="stSidebar"] {
                background-color: #EDF1F7 !important;
                border-right: 1px solid #D1D9E6 !important;
            }

            /* 3. Kartlar ve Kutular (Gördüğün o siyah alanları temizler) */
            .custom-header, div[style*="background-color"], .stExpander, div[data-testid="stExpander"] {
                background-color: #FFFFFF !important;
                background: #FFFFFF !important;
                color: #2D3436 !important;
                border-radius: 12px !important;
                border: 1px solid #E2E8F0 !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
            }

            /* 4. Inputlar (Hedef/Çözülen alanları) - En çok göz yoran yerler */
            input, .stTextInput div, [data-baseweb="input"] {
                background-color: #F1F4F8 !important;
                color: #2D3436 !important;
                border-radius: 8px !important;
                border: none !important;
            }
            
            /* 5. Yazı Renklerini Zorla Düzenle */
            h1, h2, h3, p, span, label, .stMarkdown {
                color: #2D3436 !important;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
            }

            /* 6. Video ve İlerleme Çubuğu Alanları */
            div[style*="background-color: #1c2128"] {
                background-color: #F8FAFC !important;
                border: 1px solid #E2E8F0 !important;
            }

            /* 7. Butonlar - Modern Görünüm */
            button[kind="secondary"] {
                background-color: #FFFFFF !important;
                border: 1px solid #D1D9E6 !important;
                color: #4A5568 !important;
                transition: all 0.3s !important;
            }
            button[kind="secondary"]:hover {
                border-color: #3B82F6 !important;
                color: #3B82F6 !important;
            }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.session_state.theme = 'dark'
    st.markdown("<hr style='margin:1px 0px;'>", unsafe_allow_html=True)
    if st.button("❌ Hesabımı Sil", type="secondary", use_container_width=True):
        st.session_state.confirm_delete = True
    if st.session_state.get('confirm_delete', False):
        st.warning("Verileriniz kalıcı olarak silinecektir!")
        col_del1, col_del2 = st.columns(2)
        if col_del1.button("EVET", type="primary", use_container_width=True):
            delete_user_account(all_db, username) # Bu fonksiyonun yukarıda tanımlı olduğundan emin ol
            st.toast("Hesabınız silindi.", icon="🗑️")
            st.session_state.user = None
            st.session_state.confirm_delete = False
            time.sleep(2)
            st.rerun()
        if col_del2.button("İPTAL", use_container_width=True):
            st.session_state.confirm_delete = False
            st.rerun()
menu = st.sidebar.radio("Gezinti", ["📅 Günlük Planım", "📝 Plan Oluştur", "🏆 Başarılarım"])
st.markdown('<div class="custom-header"><h1>🚀 <span style="color: #58a6ff;">2026 KPSS</span> ÇALIŞMA PLANI</h1></div>', unsafe_allow_html=True)

# --- 6. PLAN OLUŞTUR ---
if menu == "📝 Plan Oluştur":
    st.subheader("📝 Yeni Çalışma Planı")
    with st.expander("➕ Yeni Ders Ekle", expanded=False):
        c_add1, c_add2, c_add3 = st.columns([5, 1, 1.5])
        with c_add1: n_d = st.text_input("Ders Adı", placeholder="Örn: Vatandaşlık", label_visibility="collapsed")
        with c_add2:
            with st.popover(st.session_state.selected_icon, use_container_width=True):
                emos = ["📚", "📐", "🏛️", "🌍", "📰", "⚖️", "🧪", "🎨", "💻", "⏰", "💡", "📝", "✅", "🔥", "📌"]
                cols = st.columns(4)
                for i, emo in enumerate(emos):
                    if cols[i % 4].button(emo, key=f"emo_{i}"):
                        st.session_state.selected_icon = emo; st.rerun()
        with c_add3:
            if st.button("Ekle", use_container_width=True, type="primary"):
                if n_d: st.session_state.dersler[n_d] = st.session_state.selected_icon; st.rerun()
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        d_s = st.selectbox("Ders", list(st.session_state.dersler.keys()))
        k_a = st.text_input("Konu")
    with c2:
        t_r = st.date_input("Tarih", format="DD/MM/YYYY")
        s_h = st.number_input("Hedef Soru", min_value=1, value=50)

    v_s = st.select_slider("Video Sayısı", options=range(1, 11), value=1)
    
    # clear_on_submit sayesinde butona basınca kutular boşalır
    with st.form("plan_form_ana", clear_on_submit=True):
        v_u = [st.text_input(f"Video {i+1} Linki", key=f"ufin_{i}") for i in range(v_s)]
        
        submit_btn = st.form_submit_button("🚀 Planı Kaydet ve Listeye Ekle", use_container_width=True)
        
        if submit_btn:
            if k_a:
                v_d = json.dumps([{"url": format_yt_link(u), "done": False} for u in v_u if u.strip()])
                n_p = pd.DataFrame([{
                    "username": username, "password": user_df['password'].values[0],
                    "ders": d_s, "konu": k_a, "tarih": str(t_r), "videolar": v_d,
                    "soru_hedef": int(s_h), "soru_cozulen": 0, "tamamlandi": False, "id": int(datetime.now().timestamp())
                }])
                save_to_gsheets(pd.concat([all_db, n_p], ignore_index=True))
                
                # Geri bildirimler
                st.toast(f"✅ {k_a} başarıyla planlandı!", icon="📅")
                st.success("Plan eklendi! Liste güncelleniyor...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Lütfen bir konu ismi girin!")

# --- 7. GÜNLÜK PLANIM ---
elif menu == "📅 Günlük Planım":
    col_t, col_tog = st.columns([4, 1.2])
    with col_t: st.subheader("🎯 Bugünkü Görevlerin")
    with col_tog: show_history = st.toggle("✅ Tamamlananlar") 

    if show_history:
        archive_df = user_df[(user_df['tamamlandi'] == True) & (user_df['konu'] != "Hesap Aktif")]
        if not archive_df.empty:
            st.markdown("### 📜 Tamamlanan Planlar")
            for idx, row in archive_df.sort_values(by="tarih", ascending=False).iterrows():
                c_arc_text, c_arc_rev, c_arc_del = st.columns([4, 0.8, 0.8])
                with c_arc_text:
                    st.markdown(f'<div class="history-item"><b>{row["ders"]}</b>:   {row["konu"]}    <small>({row["tarih"]})</small></div>', unsafe_allow_html=True)
                with c_arc_rev:
                    if st.button("⏪", key=f"rev_{row['id']}", help="Geri Al", use_container_width=True):
                        v_list = json.loads(row['videolar']) if isinstance(row['videolar'], str) else []
                        for v in v_list: v['done'] = False
                        all_db.loc[all_db['id'] == row['id'], 'videolar'] = json.dumps(v_list)
                        all_db.loc[all_db['id'] == row['id'], 'tamamlandi'] = False
                        save_to_gsheets(all_db);
                        st.toast(f"{row['konu']} tekrar çalışma planına eklendi.", icon="⏪") # Pop-up bildirim
                        time.sleep(1)
                        st.rerun()
                with c_arc_del:
                    if st.button("🗑️", key=f"del_arc_{row['id']}", help="Sil", use_container_width=True):
                        save_to_gsheets(all_db[all_db['id'] != row['id']]);
                        st.toast(f"{row['konu']} başarıyla sildiniz.", icon="🗑️") # Pop-up bildirim
                        time.sleep(1)
                        st.rerun()
            st.divider()

    active_df = user_df[(user_df['tamamlandi'] == False) & (user_df['konu'] != "Hesap Aktif")]
    if active_df.empty: st.info("Aktif görev yok.")
    else:
        for idx, row in active_df.iterrows():
            ikon = st.session_state.dersler.get(row['ders'], "📌")
            with st.expander(f"{ikon} {row['ders']} - {row['konu']}", expanded=True):
                v_l = json.loads(row['videolar']) if isinstance(row['videolar'], str) else []
                cl, cr = st.columns([4, 1.5])
                with cl:
                    if v_l:
                        num_v = len(v_l); v_cols_num = 2 if num_v <= 2 else (3 if num_v <= 6 else 5)
                        v_cols = st.columns(v_cols_num)
                        for v_i, v in enumerate(v_l):
                            with v_cols[v_i % v_cols_num]:
                                if not v['done']:
                                    st.markdown(f"""
                                        <div class="video-container">
                                            <div class="video-label-bar">{v_i+1}. Video</div>
                                            <div class="video-body">
                                    """, unsafe_allow_html=True)
                                    st.video(v['url'])
                                    st.markdown('</div></div>', unsafe_allow_html=True)
                                    if st.button(f"İzlendi ✅", key=f"v_{row['id']}_{v_i}", use_container_width=True):
                                        v['done'] = True
                                        all_db.loc[all_db['id'] == row['id'], 'videolar'] = json.dumps(v_l)
                                        save_to_gsheets(all_db); st.rerun()
                                else: st.success(f"{v_i+1}. Video Bitti")
                with cr:
                    h_q = int(row['soru_hedef']); c_q = int(row['soru_cozulen'])
                    yuzde = int((c_q / h_q) * 100) if h_q > 0 else 0
                    st.markdown(f"**Hedef:** `{h_q}`")
                    n_q = st.number_input("Çözülen", value=c_q, key=f"q_{row['id']}")
                    if n_q != c_q:
                        all_db.loc[all_db['id'] == row['id'], 'soru_cozulen'] = int(n_q)
                        save_to_gsheets(all_db); st.rerun()
                    st.markdown(f"**İlerleme:** `%{yuzde}`"); st.progress(min(yuzde/100, 1.0)); st.divider()
                    if st.button("🌟 GÖREVİ TAMAMLA", key=f"f_{row['id']}", use_container_width=True, type="primary"):
                        for v in v_l: v['done'] = False
                        all_db.loc[all_db['id'] == row['id'], 'videolar'] = json.dumps(v_l)
                        all_db.loc[all_db['id'] == row['id'], 'tamamlandi'] = True
                        save_to_gsheets(all_db)
                        st.balloons() # Konfetiler
                        st.toast(f"Tebrikler! {row['konu']} konusunu bitirdin!", icon="🏆") # Pop-up bildirim
                        time.sleep(1)
                        st.rerun()
                    if st.button("🗑️ Planı Sil", key=f"del_act_{row['id']}", use_container_width=True):
                        save_to_gsheets(all_db[all_db['id'] != row['id']]);
                        st.toast(f"{row['konu']} konusunu sildiniz!", icon="🗑️") # Pop-up bildirim
                        time.sleep(1)
                        st.rerun()

# --- 8. BAŞARILARIM ---
elif menu == "🏆 Başarılarım":
    bitenler = user_df[(user_df['tamamlandi'] == True) & (user_df['konu'] != "Hesap Aktif")]
    st.markdown("### 📊 Genel Başarı Tablon")
    c_m1, c_m2 = st.columns(2)
    with c_m1: st.markdown(f'<div class="stat-card"><h2>🔥 {int(bitenler["soru_cozulen"].sum())}</h2>Soru Çözüldü</div>', unsafe_allow_html=True)
    with c_m2: st.markdown(f'<div class="stat-card"><h2>✅ {len(bitenler)}</h2>Konu Tamamlandı</div>', unsafe_allow_html=True)
    st.divider()

    for d, ikon in st.session_state.dersler.items():
        ders_df = user_df[user_df['ders'] == d]
        if not ders_df.empty:
            b_df = ders_df[ders_df['tamamlandi'] == True]
            toplam_video = 0
            for _, r in b_df.iterrows():
                v_data = json.loads(r['videolar']) if isinstance(r['videolar'], str) else []
                toplam_video += len(v_data)
            y = int((len(b_df)/len(ders_df))*100) if len(ders_df) > 0 else 0
            st.markdown(f"### {ikon} {d} (%{y})")
            st.progress(y/100)
            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric("Biten Konu", len(b_df))
            col_d2.metric("Toplam Soru", int(b_df['soru_cozulen'].sum()))
            col_d3.metric("İzlenen Video", toplam_video)
            with st.expander(f"{d} Detayları"):
                for _, b in b_df.iterrows():
                    v_say = len(json.loads(b['videolar'])) if isinstance(b['videolar'], str) else 0
                    st.markdown(f'<div class="success-card"><b>{b["konu"]}</b><br><small>📝 {int(b["soru_cozulen"])} Soru | 📺 {v_say} Video | 📅 {b["tarih"]}</small></div>', unsafe_allow_html=True)













































