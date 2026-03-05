import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import hashlib
from datetime import datetime
import time
from streamlit_lottie import st_lottie
import requests


# --- 1. VERİ BAĞLANTISI & OPTİMİZASYON ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def load_all_data():
    try:
        df = conn.read()
        if df is None or df.empty:
            return pd.DataFrame(columns=["username", "password", "ders", "konu", "tarih", "videolar", "soru_hedef", "soru_cozulen", "tamamlandi", "id", "display_name"])
        # --- TEMİZLİK BURADA YAPILIYOR ---
        # 1. Tamamen boş satırları sil
        df = df.dropna(how="all")
        # 2. Kullanıcı adı (username) boş olan satırları sil
        df = df.dropna(subset=["username"])
        # 3. 'display_name' sütunu yoksa oluştur (çökmeyi önlemek için)
        if 'display_name' not in df.columns:
            df['display_name'] = df['username']
        return df
    except:
        return pd.DataFrame(columns=["username", "password", "ders", "konu", "tarih", "videolar", "soru_hedef", "soru_cozulen", "tamamlandi", "id", "display_name"])

def save_to_gsheets(df):
    conn.update(data=df)
    st.cache_data.clear() # Değişiklik olduğunda cache'i temizle

def hash_password(password):
    pepper = st.secrets.get("security", {}).get("pepper", "")
    salted_password = f"{password}{pepper}"
    return hashlib.sha256(str.encode(salted_password)).hexdigest()

def format_yt_link(url):
    url = url.strip()
    return url if url.startswith("http") else f"https://{url}" if url else ""

def delete_user_account(df, username):
    new_df = df[df['username'] != username]
    save_to_gsheets(new_df)
    st.cache_data.clear()
    
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None
        
# Load Lottie animations
lottie_celebration = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_u4yrau.json")

st.set_page_config(page_title="2026 KPSS ÇALIŞMA PLANI", layout="wide", page_icon="🎓")
# --- 0. SESSION STATE BAŞLATMA ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False

# --- 3. VERİ ÇEKME VE TİP DÖNÜŞÜMÜ ---
all_db = load_all_data()

for col in ['tamamlandi', 'id', 'soru_cozulen', 'soru_hedef']:
    if col in all_db.columns:
        if col == 'tamamlandi':
            all_db[col] = all_db[col].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False, '1.0': True, '0.0': False}).fillna(False)
        else:
            all_db[col] = pd.to_numeric(all_db[col], errors='coerce').fillna(0 if col != 'soru_hedef' else 1).astype(int)

if 'selected_icon' not in st.session_state: st.session_state.selected_icon = "📌"
if 'dersler' not in st.session_state:
    st.session_state.dersler = {"Matematik": "📐", "Türkçe": "📚", "Tarih": "🏛️", "Coğrafya": "🌍", "Güncel Bilgiler": "📰"}

# --- 4. GİRİŞ KONTROLÜ ---
if st.session_state.user is None:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: white; margin-bottom: 0;">🚀 2026 KPSS Çalışma Planı Giriş</h1>
        <hr style="border: 1px solid #fe4a49; width: 50%; margin: auto;">
    </div>
    """, unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with t1:
        with st.form("login_form_unique"):
            u = st.text_input("Kullanıcı Adı", key="login_u").strip()
            p = st.text_input("Şifre", type="password", key="login_p").strip()
            
            if st.form_submit_button("Sisteme Bağlan", use_container_width=True):
                if u and p: # Boş giriş kontrolü
                    user_check = all_db[(all_db['username'].fillna("").astype(str) == str(u)) & 
                                        (all_db['password'].fillna("").astype(str) == hash_password(str(p)))]
                    
                if not user_check.empty:
                    st.session_state.user = str(u)
                    if 'puan_hedef' in user_check.columns:
                        mevcut_hedef = user_check['puan_hedef'].iloc[0]
                        if pd.isna(mevcut_hedef):
                            mevcut_hedef = 0.0

                    st.success(f"Hoş geldin {u}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")
    with t2:
        with st.form("reg_form_unique"):
            nu = st.text_input("Yeni Kullanıcı Adı", key="reg_user_input").strip()
            np = st.text_input("Yeni Şifre", type="password", key="reg_pass_input").strip()
            if st.form_submit_button("Hesap Oluştur", use_container_width=True):
                if nu in all_db['username'].values: st.error("Bu kullanıcı mevcut.")
                else:
                    new_u_row = pd.DataFrame([{"username": nu, "display_name": nu, "password": hash_password(np), "tamamlandi": False, "id": int(time.time()), "konu": "Hesap Aktif", "soru_cozulen": 0, "soru_hedef": 1, "puan_hedef": 0.0, "ders": "Genel"}])
                    save_to_gsheets(pd.concat([all_db, new_u_row], ignore_index=True))
                    st.success("Kayıt başarılı!")
    st.stop()

# --- 5. ANA EKRAN ---
username = st.session_state.user
user_df = all_db[all_db['username'].astype(str) == str(username)].copy()
if not user_df.empty and 'puan_hedef' in user_df.columns:
    val = user_df['puan_hedef'].iloc[0]
    mevcut_hedef = float(val) if pd.notna(val) else 0.0
else:
    mevcut_hedef = 0.0
    
# --- GÜVENLİ İSİM ÇEKME BLOĞU ---
if not user_df.empty:
    # Kullanıcı bulunduysa, display_name sütunu var mı ve içi dolu mu bak
    if 'display_name' in user_df.columns and pd.notna(user_df['display_name'].iloc[0]):
        d_name = user_df['display_name'].iloc[0]
    else:
        # Sütun yoksa veya içi boşsa giriş adını (username) kullan
        d_name = username
else:
    # Eğer user_df tamamen boşsa (giriş hatası veya veri çekme gecikmesi)
    d_name = username
    
# Artık d_name değişkeni her durumda dolu, hata vermez:
st.sidebar.markdown(f"### 👤 {d_name}")
st.sidebar.caption(f"@{username}")
st.sidebar.markdown("""
    <hr style="margin-top: 5px; margin-bottom: 5px; border: 0; border-top: 1px solid #444; opacity: 0.5;">
""", unsafe_allow_html=True)
st.sidebar.markdown("""
    <style>
        /* Sidebar'ın ana konteynerini flex yap ve ortala */
        [data-testid="stSidebarUserContent"] {
            display: fix;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 15vh; /* Neredeyse tüm ekran boyu */
        }
        /* Metinleri ve başlıkları ortala */
        [data-testid="stSidebarUserContent"] .stMarkdown, 
        [data-testid="stSidebarUserContent"] .stCaption {
            text-align: center;
            width: 100%;
        }
        /* Menü seçeneklerini (Radio buttons) ortala */
        [data-testid="stSidebarNavItems"], [data-testid="stWidgetLabel"] {
            display: flex;;
            justify-content: center;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)
menu = st.sidebar.radio("", ["📅 Günlük Planım", "📝 Plan Oluştur", "🏆 Başarılarım", "📊 Deneme Takibi"])
with st.sidebar.expander("⚙️ Hesap Ayarları"):
    st.subheader("Profil Düzenle")
    
    current_display_name = user_df['display_name'].iloc[0] if 'display_name' in user_df.columns else username
    yeni_display = st.text_input("Ekranda Görünecek Adın", value=current_display_name)
    
    if st.button("Görünen Adı Güncelle"):
        all_db.loc[all_db['username'] == username, 'display_name'] = yeni_display
        save_to_gsheets(all_db)
        st.success("İsim güncellendi!")
        st.rerun()
        
    # 2. Hedef Puan Belirleme
    mevcut_hedef = user_df['puan_hedef'].iloc[0] if 'puan_hedef' in user_df.columns else 0
    yeni_hedef = st.number_input("Hedef KPSS Puanı", min_value=0.0, max_value=100.0, value=float(mevcut_hedef), step=0.5)
    if st.button("Hedefi Kaydet"):
        all_db.loc[all_db['username'] == username, 'puan_hedef'] = yeni_hedef
        save_to_gsheets(all_db)
        st.success("Hedef puan güncellendi! 🎯")
    if st.button("❌ Hesabımı Sil", type="secondary", use_container_width=True):
        st.session_state.confirm_delete = True
    if st.session_state.get('confirm_delete', False):
        st.warning("Verileriniz kalıcı olarak silinecektir!")
        col_del1, col_del2 = st.columns(2)
        if col_del1.button("EVET", type="primary", use_container_width=True):
            delete_user_account(all_db, username)
            st.toast("Hesabınız silindi.", icon="🗑️")
            st.session_state.user = None
            st.session_state.confirm_delete = False
            time.sleep(2)
            st.rerun()
        if col_del2.button("İPTAL", use_container_width=True):
            st.session_state.confirm_delete = False
            st.rerun()
if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
    st.session_state.user = None
    st.rerun()
    # Sidebar elemanlarını dikeyde ortalamak için CSS
    st.sidebar.markdown("""
        <style>
            /* Sidebar'ın içindeki ana alanı seçiyoruz */
            [data-testid="stSidebarNavItems"] {
                display: flex;
                flex-direction: column;
                justify-content: center;
                height: 70vh; /* Ekran yüksekliğinin %70'ini kapla */
            }
            
            /* Kullanıcı adı ve ikon kısmını da merkeze odakla */
            section[data-testid="stSidebar"] .stMarkdown {
                text-align: center;
            }
            
            /* Butonları genişlet ve hizala */
            section[data-testid="stSidebar"] .stButton button {
                width: 100%;
            }
        </style>
    """, unsafe_allow_html=True)
st.markdown("""
    <div class="custom-header"; style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: white; margin-bottom: 0;">🚀 2026 KPSS Çalışma Planım</h1>
        <hr style="border: 2px solid #88c3f7; width: 50%; margin: auto; opacity: 0,7;">
        <hr style="border: 4px solid #3d9df3; width: 50%; bottom: 2px; margin: auto; opacity: 0,3;">
    </div>
    """, unsafe_allow_html=True)

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
    
    st.markdown("<hr style='margin:2px 0px;'>", unsafe_allow_html=True)
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
        archive_df = user_df[(user_df['tamamlandi'] == True) & (user_df['ders'] != "DENEME") & (user_df['konu'] != "Hesap Aktif")]
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
            st.markdown("<hr style='margin:2px 0px;'>", unsafe_allow_html=True)

    active_df = user_df[(user_df['tamamlandi'] == False) & (user_df['ders'] != "DENEME") & (user_df['konu'] != "Hesap Aktif")]
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
                    # 1. Veri Hazırlığı
                    h_q = int(row['soru_hedef'])
                    c_q = int(row['soru_cozulen'])
                    yuzde_f = min(c_q / h_q, 1.0) if h_q > 0 else 0.0
                    st.write(f"📊 **İlerleme: %{int(yuzde_f * 100)}**")
                    st.progress(yuzde_f)
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Hedef", h_q)
                    col_m2.metric("Çözülen", c_q, delta=c_q - h_q if h_q > 0 else None)
                    n_q = st.number_input("Sayıyı Güncelle", value=c_q, key=f"q_{row['id']}", label_visibility="collapsed")
                    if n_q != c_q:
                        all_db.loc[all_db['id'] == row['id'], 'soru_cozulen'] = int(n_q)
                        save_to_gsheets(all_db)
                        st.rerun()
                    st.markdown("<hr style='margin:1px 0px;'>", unsafe_allow_html=True)
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
    st.markdown("<hr style='margin:2px 0px;'>", unsafe_allow_html=True)

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
elif menu == "📊 Deneme Takibi":
    st.subheader("📊 Deneme Netleri ve Puan Hesaplama")
    
    # Hedef Puanı Veriden Çek (Varsayılan 75.0)
    user_settings = all_db[all_db['username'] == username]
    hedef_puan = float(user_settings['puan_hedef'].iloc[0]) if 'puan_hedef' in user_settings.columns and not pd.isna(user_settings['puan_hedef'].iloc[0]) else 75.0

    # 1. YENİ DENEME HESAPLAMA FORMU
    with st.expander("➕ Yeni Deneme Hesapla ve Kaydet", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            gk_d = st.number_input("GK Doğru", 0, 60, 0, key="new_gk_d")
            gk_y = st.number_input("GK Yanlış", 0, 60, 0, key="new_gk_y")
        with c2:
            gy_d = st.number_input("GY Doğru", 0, 60, 0, key="new_gy_d")
            gy_y = st.number_input("GY Yanlış", 0, 60, 0, key="new_gy_y")
        
        gk_net = gk_d - (gk_y * 0.25)
        gy_net = gy_d - (gy_y * 0.25)
        # KPSS P3 Yaklaşık Formül: 40 + (Toplam Net * 0.5)
        hesaplanan_puan = 40 + ((gk_net + gy_net) * 0.5)
        
        st.success(f"🧮 Netlerin: **{gk_net + gy_net}** | Tahmini Puan: **{hesaplanan_puan:.3f}**")
        
        d_ad = st.text_input("Deneme Adı/Yayın", placeholder="Örn: Pegem TG-1")
        if st.button("🚀 Denemeyi Arşive Kaydet", use_container_width=True):
            if d_ad:
                gk_net = gk_d - (gk_y * 0.25)
                gy_net = gy_d - (gy_y * 0.25)
                hesaplanan_puan = 40 + ((gk_net + gy_net) * 0.5)
                if hesaplanan_puan >= hedef_puan:
                    st.balloons()
                yeni_deneme = pd.DataFrame([{
                "username": username, 
                "password": user_df['password'].values[0],
                "ders": "DENEME", 
                "konu": d_ad, 
                "tarih": str(datetime.now().date()),
                "deneme_gk_d": gk_d, 
                "deneme_gk_y": gk_y, 
                "deneme_gy_d": gy_d, 
                "deneme_gy_y": gy_y,
                "deneme_puan": float(hesaplanan_puan), # Puanı sayı olarak kaydet
                "puan_hedef": float(hedef_puan),
                "tamamlandi": True, 
                "id": int(datetime.now().timestamp()),
                "videolar": "[]", # Burayı boş liste bırakıyoruz
                "soru_cozulen": int(gk_net + gy_net),
                "soru_hedef": 120
        }])
                # Mevcut veritabanına ekle ve gönder
                save_to_gsheets(pd.concat([all_db, yeni_deneme], ignore_index=True))
                st.toast(f"✅ {d_ad} başarıyla kaydedildi!", icon="🚀")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Lütfen deneme adını giriniz!")
    st.markdown("<hr style='margin:2px 0px;'>", unsafe_allow_html=True)
    # 2. KAYDEDİLEN DENEMELER VE ANALİZ
    st.subheader("📜 Deneme Arşivim")
    deneme_gecmisi = all_db[(all_db['username'] == username) & (all_db['ders'] == "DENEME")].sort_values(by="id", ascending=False)

    if deneme_gecmisi.empty:
        st.info("Henüz kaydedilmiş bir deneme yok.")
    else:
        for _, d_row in deneme_gecmisi.iterrows():
            puan = float(d_row.get('deneme_puan', 0))
            h_puan = float(d_row.get('puan_hedef', 85))
            fark = puan - h_puan
                # Motivasyon Mesajı Belirleme
            if fark >= 0:
                st.success("🎉 HEDEFİNE ULAŞTIN TEBRİKLER! 🎉")
                msg = "🔥 Mükemmel! Hedefin üzerindesin, bu iş bitti!"
                color = "#238636"
            elif fark >= -10:
                msg = "💪 Çok yakınsın! Küçük bir gayretle hedef elinde."
                color = "#9df000"
            elif fark >= -20:
                msg = "✍️ İşleri sıkı tut! Hedefine yaklaşıyorsun."
                color = "#ffa500"
            else:
                msg = "🚀 Yolun başındasın, pes etme; her deneme bir basamak!"
                color = "#f85149"
                
            with st.container(border=True):
                col_bilgi, col_puan, col_islem = st.columns([3, 2, 1])
                with col_bilgi:
                    st.markdown(f"**{d_row['konu']}**")
                    st.markdown("<div style='margin-bottom: -10px;'></div>", unsafe_allow_html=True)
                    st.caption(f"📅 {d_row['tarih']}")
                    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                    st.write(f"GK: {d_row['deneme_gk_d']}D {d_row['deneme_gk_y']}Y | GY: {d_row['deneme_gy_d']}D {d_row['deneme_gy_y']}Y")
                    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                with col_puan:
                    st.markdown(f"""
                        <div style="text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                            <h2 style="margin-top: -5px; color: {color}; font-size: 2.2rem;">{puan:.2f}</h2>
                            <p style="margin: 0px; opacity: 0.6; font-size: 1rem;">Hedefe Uzaklık: {fark:.2f}</p>
                            <div style="margin-top: 10px;"></div>
                            <p style="font-style: italic; font-size: 1.1rem; color: {color}; font-weight: 500;">{msg}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col_islem:
                    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_deneme_{d_row['id']}", use_container_width=True):
                        save_to_gsheets(all_db[all_db['id'] != d_row['id']])
                        st.toast("🗑️  Deneme silindi.")
                        time.sleep(1)
                        st.rerun()


















