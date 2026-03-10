import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import hashlib
from datetime import datetime
import time

# ============================================================
# 1. SAYFA YAPILANDIRMASI (En başta olmalı)
# ============================================================
st.set_page_config(page_title="2026 KPSS ÇALIŞMA PLANI", layout="wide", page_icon="🎓")

# ============================================================
# 2. VERİ BAĞLANTISI
# ============================================================
conn = st.connection("gsheets", type=GSheetsConnection)

# ============================================================
# 3. YARDIMCI FONKSİYONLAR
# ============================================================

def hash_password(password: str) -> str:
    pepper = st.secrets.get("security", {}).get("pepper", "")
    salted = f"{password}{pepper}"
    return hashlib.sha256(salted.encode()).hexdigest()

def format_yt_link(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    return url if url.startswith("http") else f"https://{url}"

def get_user_password(user_df: pd.DataFrame) -> str:
    """Güvenli şifre hash erişimi — IndexError önler."""
    if not user_df.empty and 'password' in user_df.columns:
        return str(user_df['password'].values[0])
    return ""

def safe_float(val, default: float = 0.0) -> float:
    """NaN / None / boş değerleri güvenle float'a çevirir."""
    try:
        result = float(val)
        return default if pd.isna(result) else result
    except (TypeError, ValueError):
        return default

def safe_int(val, default: int = 0) -> int:
    """NaN / None / boş değerleri güvenle int'e çevirir."""
    try:
        result = float(val)
        return default if pd.isna(result) else int(result)
    except (TypeError, ValueError):
        return default

# ============================================================
# 4. VERİ OKUMA / YAZMA (Cache optimized)
# ============================================================

@st.cache_data(ttl=30)
def load_all_data() -> pd.DataFrame:
    default_cols = [
        "username", "password", "ders", "konu", "tarih", "videolar",
        "soru_hedef", "soru_cozulen", "tamamlandi", "id",
        "display_name", "puan_hedef",
        "deneme_gk_d", "deneme_gk_y", "deneme_gy_d", "deneme_gy_y", "deneme_puan"
    ]
    try:
        df = conn.read()
        if df is None or df.empty:
            return pd.DataFrame(columns=default_cols)

        df = df.dropna(how="all").dropna(subset=["username"])

        # --- Sütun eksikliği garantisi ---
        for col in default_cols:
            if col not in df.columns:
                df[col] = None

        # --- Boolean dönüşüm ---
        bool_map = {'true': True, 'false': False, '1': True, '0': False,
                    '1.0': True, '0.0': False}
        df['tamamlandi'] = (
            df['tamamlandi'].astype(str).str.lower()
            .map(bool_map).fillna(False)
        )

        # --- Sayısal dönüşümler ---
        df['id']           = pd.to_numeric(df['id'],           errors='coerce').fillna(0).astype(int)
        df['soru_cozulen'] = pd.to_numeric(df['soru_cozulen'], errors='coerce').fillna(0).astype(int)
        df['soru_hedef']   = pd.to_numeric(df['soru_hedef'],   errors='coerce').fillna(1).astype(int)
        df['puan_hedef']   = pd.to_numeric(df['puan_hedef'],   errors='coerce').fillna(0.0)
        df['deneme_puan']  = pd.to_numeric(df['deneme_puan'],  errors='coerce').fillna(0.0)

        for col in ['deneme_gk_d', 'deneme_gk_y', 'deneme_gy_d', 'deneme_gy_y']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # --- display_name boş olanları username ile doldur ---
        mask = df['display_name'].isna() | (df['display_name'].astype(str).str.strip() == '')
        df.loc[mask, 'display_name'] = df.loc[mask, 'username']

        return df

    except Exception as e:
        st.warning(f"Veri yüklenirken hata oluştu: {e}")
        return pd.DataFrame(columns=default_cols)


def save_to_gsheets(df: pd.DataFrame):
    """Veritabanını kaydeder ve SADECE load_all_data cache'ini temizler."""
    conn.update(data=df)
    load_all_data.clear()   # FIX: st.cache_data.clear() yerine spesifik temizleme


# ============================================================
# 5. SESSION STATE BAŞLATMA
# ============================================================
if 'user'           not in st.session_state: st.session_state.user           = None
if 'confirm_delete' not in st.session_state: st.session_state.confirm_delete  = False
if 'selected_icon'  not in st.session_state: st.session_state.selected_icon   = "📌"
if 'dersler'        not in st.session_state:
    st.session_state.dersler = {
        "Matematik": "📐", "Türkçe": "📚", "Tarih": "🏛️",
        "Coğrafya": "🌍", "Güncel Bilgiler": "📰"
    }

# ============================================================
# 6. VERİ ÇEKME
# ============================================================
all_db = load_all_data()

# ============================================================
# 7. GİRİŞ / KAYIT EKRANI
# ============================================================
if st.session_state.user is None:
    st.markdown("""
    <div style="text-align:center; margin-bottom:20px;">
        <h1 style="color:white; margin-bottom:0;">🚀 2026 KPSS Çalışma Planı Giriş</h1>
        <hr style="border:1px solid #fe4a49; width:50%; margin:auto;">
    </div>
    """, unsafe_allow_html=True)

    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])

    with t1:
        with st.form("login_form"):
            u = st.text_input("Kullanıcı Adı").strip()
            p = st.text_input("Şifre", type="password").strip()
            if st.form_submit_button("Sisteme Bağlan", use_container_width=True):
                if u and p:
                    match = all_db[
                        (all_db['username'].fillna("").astype(str) == u) &
                        (all_db['password'].fillna("").astype(str) == hash_password(p))
                    ]
                    if not match.empty:
                        st.session_state.user = u
                        st.success(f"Hoş geldin {u}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Kullanıcı adı veya şifre hatalı!")
                else:
                    st.warning("Kullanıcı adı ve şifre boş bırakılamaz!")

    with t2:
        with st.form("reg_form"):
            nu = st.text_input("Yeni Kullanıcı Adı").strip()
            np = st.text_input("Yeni Şifre", type="password").strip()
            if st.form_submit_button("Hesap Oluştur", use_container_width=True):
                if not nu or not np:
                    st.warning("Kullanıcı adı ve şifre boş bırakılamaz!")
                elif nu in all_db['username'].values:
                    st.error("Bu kullanıcı adı zaten mevcut.")
                else:
                    new_row = pd.DataFrame([{
                        "username": nu, "display_name": nu,
                        "password": hash_password(np),
                        "tamamlandi": False, "id": int(time.time() * 1000),
                        "konu": "Hesap Aktif", "soru_cozulen": 0,
                        "soru_hedef": 1, "puan_hedef": 0.0, "ders": "Genel",
                        "videolar": "[]"
                    }])
                    save_to_gsheets(pd.concat([all_db, new_row], ignore_index=True))
                    st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
    st.stop()

# ============================================================
# 8. ANA EKRAN — Kullanıcı doğrulandı
# ============================================================
username = st.session_state.user
user_df  = all_db[all_db['username'] == username].copy()

# Güvenli display_name
if not user_df.empty and 'display_name' in user_df.columns:
    raw_name = user_df['display_name'].iloc[0]
    d_name = raw_name if pd.notna(raw_name) and str(raw_name).strip() else username
else:
    d_name = username

# Mevcut hedef puan
mevcut_hedef = safe_float(
    user_df['puan_hedef'].iloc[0] if not user_df.empty and 'puan_hedef' in user_df.columns else 0.0
)

# ============================================================
# 9. SIDEBAR
# ============================================================
st.sidebar.markdown(f"### 👤 {d_name}")
st.sidebar.caption(f"@{username}")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.markdown("""
<style>
[data-testid="stSidebarUserContent"] {
    margin-top: -30px !important;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center; min-height: 20vh;
}
[data-testid="stSidebarUserContent"] .stMarkdown,
[data-testid="stSidebarUserContent"] .stCaption {
    margin-top: -3px; text-align: center; width: 100%;
}
[data-testid="stVerticalBlock"] > div { margin-top:1px; gap:0.2rem !important; margin-bottom:-0.2rem !important; }
[data-testid="stExpander"] [data-testid="stVerticalBlock"] { gap:1rem !important; }
.stButton button { padding-top:0.5rem !important; padding-bottom:0.5rem !important; min-height:2rem !important; font-size:1rem !important; }
[data-testid="stWidgetLabel"] p { font-size:1rem !important; }
.stTextInput input, .stNumberInput input { padding:0.5rem !important; font-size:1rem !important; }
[data-testid="stSidebar"] { overflow:hidden !important; }
section[data-testid="stSidebar"] .stMarkdown { text-align:center; }
section[data-testid="stSidebar"] .stButton button { width:100%; }
</style>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("", ["📅 Günlük Planım", "📝 Plan Oluştur", "🏆 Başarılarım", "📊 Deneme Takibi"])

# --- Hesap Ayarları ---
with st.sidebar.expander("⚙️ Hesap Ayarları"):
    st.subheader("Profil Düzenle")

    current_display_name = str(user_df['display_name'].iloc[0]) if (
        not user_df.empty and 'display_name' in user_df.columns
        and pd.notna(user_df['display_name'].iloc[0])
    ) else username

    # FIX: "yeni_display = any" satırı kaldırıldı — artık input değeri korunuyor
    yeni_display = st.text_input("Ekranda Görünecek Adın", value=current_display_name)

    if st.button("Görünen Adı Güncelle"):
        if yeni_display.strip():
            all_db.loc[all_db['username'] == username, 'display_name'] = yeni_display.strip()
            save_to_gsheets(all_db)
            st.success("İsim güncellendi!")
            st.rerun()
        else:
            st.warning("Ad boş bırakılamaz.")

    # Hedef Puan
    yeni_hedef = st.number_input(
        "Hedef KPSS Puanı", min_value=0.0, max_value=100.0,
        value=mevcut_hedef, step=0.5
    )
    if st.button("Hedefi Kaydet"):
        all_db.loc[all_db['username'] == username, 'puan_hedef'] = yeni_hedef
        save_to_gsheets(all_db)
        st.success("Hedef puan güncellendi! 🎯")

    # Hesap Silme
    if st.button("❌ Hesabımı Sil", type="secondary", use_container_width=True):
        st.session_state.confirm_delete = True

    if st.session_state.get('confirm_delete', False):
        st.warning("Tüm verileriniz kalıcı olarak silinecektir!")
        col_del1, col_del2 = st.columns(2)
        if col_del1.button("EVET", type="primary", use_container_width=True):
            save_to_gsheets(all_db[all_db['username'] != username])
            st.toast("Hesabınız silindi.", icon="🗑️")
            st.session_state.user           = None
            st.session_state.confirm_delete = False
            time.sleep(2)
            st.rerun()
        if col_del2.button("İPTAL", use_container_width=True):
            st.session_state.confirm_delete = False
            st.rerun()

if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
    st.session_state.user = None
    st.rerun()

# --- Başlık ---
st.markdown("""
<div style="text-align:center; margin-bottom:20px;">
    <h1 style="color:white; margin-bottom:0;">🚀 2026 KPSS Çalışma Planım</h1>
    <hr style="border:2px solid #88c3f7; width:50%; margin:auto; opacity:0.7;">
    <hr style="border:4px solid #3d9df3; width:50%; bottom:2px; margin:auto; opacity:0.3;">
</div>
""", unsafe_allow_html=True)

# ============================================================
# 10. PLAN OLUŞTUR
# ============================================================
if menu == "📝 Plan Oluştur":
    st.subheader("📝 Yeni Çalışma Planı")

    with st.expander("➕ Yeni Ders Ekle", expanded=False):
        c_add1, c_add2, c_add3 = st.columns([5, 1, 1.5])
        with c_add1:
            n_d = st.text_input("Ders Adı", placeholder="Örn: Vatandaşlık",
                                label_visibility="collapsed")
        with c_add2:
            with st.popover(st.session_state.selected_icon, use_container_width=True):
                emos = ["📚","📐","🏛️","🌍","📰","⚖️","🧪","🎨","💻","⏰","💡","📝","✅","🔥","📌"]
                cols = st.columns(4)
                for i, emo in enumerate(emos):
                    if cols[i % 4].button(emo, key=f"emo_{i}"):
                        st.session_state.selected_icon = emo
                        st.rerun()
        with c_add3:
            if st.button("Ekle", use_container_width=True, type="primary"):
                if n_d.strip():
                    st.session_state.dersler[n_d.strip()] = st.session_state.selected_icon
                    st.rerun()
                else:
                    st.warning("Ders adı boş olamaz.")

    st.markdown("<hr style='margin:2px 0px;'>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        d_s = st.selectbox("Ders", list(st.session_state.dersler.keys()))
        k_a = st.text_input("Konu")
    with c2:
        t_r = st.date_input("Tarih", format="DD/MM/YYYY")
        s_h = st.number_input("Hedef Soru", min_value=1, value=50)

    v_s = st.select_slider("Video Sayısı", options=range(1, 11), value=1)

    with st.form("plan_form", clear_on_submit=True):
        v_u = [st.text_input(f"Video {i+1} Linki", key=f"vlink_{i}") for i in range(v_s)]
        if st.form_submit_button("🚀 Planı Kaydet ve Listeye Ekle", use_container_width=True):
            if k_a.strip():
                v_d = json.dumps([
                    {"url": format_yt_link(u), "done": False}
                    for u in v_u if u.strip()
                ])
                new_plan = pd.DataFrame([{
                    "username":    username,
                    "password":    get_user_password(user_df),  # FIX: güvenli erişim
                    "display_name": d_name,
                    "ders":        d_s,
                    "konu":        k_a.strip(),
                    "tarih":       str(t_r),
                    "videolar":    v_d,
                    "soru_hedef":  int(s_h),
                    "soru_cozulen": 0,
                    "tamamlandi":  False,
                    "id":          int(time.time() * 1000),
                    "puan_hedef":  mevcut_hedef
                }])
                save_to_gsheets(pd.concat([all_db, new_plan], ignore_index=True))
                st.toast(f"✅ {k_a} başarıyla planlandı!", icon="📅")
                st.success("Plan eklendi!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Lütfen bir konu ismi girin!")

# ============================================================
# 11. GÜNLÜK PLANIM
# ============================================================
elif menu == "📅 Günlük Planım":
    col_t, col_tog = st.columns([4, 1.2])
    with col_t:
        st.subheader("🎯 Bugünkü Görevlerin")
    with col_tog:
        show_history = st.toggle("✅ Tamamlananlar")

    # --- Tamamlanan arşiv ---
    if show_history:
        archive_df = user_df[
            (user_df['tamamlandi'] == True) &
            (user_df['ders'] != "DENEME") &
            (user_df['konu'] != "Hesap Aktif")
        ]
        if not archive_df.empty:
            st.markdown("### 📜 Tamamlanan Planlar")
            for _, row in archive_df.sort_values("tarih", ascending=False).iterrows():
                c_text, c_rev, c_del = st.columns([4, 0.8, 0.8])
                with c_text:
                    st.markdown(
                        f'<div><b>{row["ders"]}</b>: {row["konu"]} '
                        f'<small>({row["tarih"]})</small></div>',
                        unsafe_allow_html=True
                    )
                with c_rev:
                    if st.button("⏪", key=f"rev_{row['id']}", help="Geri Al",
                                 use_container_width=True):
                        v_list = json.loads(row['videolar']) if isinstance(row['videolar'], str) else []
                        for v in v_list:
                            v['done'] = False
                        all_db.loc[all_db['id'] == row['id'], 'videolar'] = json.dumps(v_list)
                        all_db.loc[all_db['id'] == row['id'], 'tamamlandi'] = False
                        save_to_gsheets(all_db)
                        st.toast(f"{row['konu']} tekrar plana eklendi.", icon="⏪")
                        time.sleep(0.3)
                        st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_arc_{row['id']}", help="Sil",
                                 use_container_width=True):
                        save_to_gsheets(all_db[all_db['id'] != row['id']])
                        st.toast(f"{row['konu']} silindi.", icon="🗑️")
                        time.sleep(0.3)
                        st.rerun()
            st.markdown("<hr style='margin:2px 0px;'>", unsafe_allow_html=True)

    # --- Aktif görevler ---
    active_df = user_df[
        (user_df['tamamlandi'] == False) &
        (user_df['ders'] != "DENEME") &
        (user_df['konu'] != "Hesap Aktif")
    ]
    if active_df.empty:
        st.info("Aktif görev yok. Plan Oluştur menüsünden yeni görev ekleyebilirsin!")
    else:
        for _, row in active_df.iterrows():
            ikon = st.session_state.dersler.get(row['ders'], "📌")
            with st.expander(f"{ikon} {row['ders']} — {row['konu']}", expanded=True):
                v_l = json.loads(row['videolar']) if isinstance(row['videolar'], str) else []
                cl, cr = st.columns([4, 1.5])

                with cl:
                    if v_l:
                        num_v = len(v_l)
                        v_cols_num = 2 if num_v <= 2 else (3 if num_v <= 6 else 5)
                        v_cols = st.columns(v_cols_num)
                        for v_i, v in enumerate(v_l):
                            with v_cols[v_i % v_cols_num]:
                                if not v.get('done', False):
                                    st.markdown(f"**{v_i+1}. Video**")
                                    if v.get('url'):
                                        st.video(v['url'])
                                    if st.button(f"İzlendi ✅", key=f"v_{row['id']}_{v_i}",
                                                 use_container_width=True):
                                        v['done'] = True
                                        all_db.loc[all_db['id'] == row['id'], 'videolar'] = json.dumps(v_l)
                                        save_to_gsheets(all_db)
                                        st.rerun()
                                else:
                                    st.success(f"{v_i+1}. Video Bitti ✅")

                with cr:
                    h_q = safe_int(row['soru_hedef'], 1)
                    c_q = safe_int(row['soru_cozulen'], 0)
                    yuzde = min(c_q / h_q, 1.0) if h_q > 0 else 0.0

                    st.write(f"📊 **İlerleme: %{int(yuzde * 100)}**")
                    st.progress(yuzde)
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Hedef", h_q)
                    col_m2.metric("Çözülen", c_q, delta=c_q - h_q if h_q > 0 else None)

                    n_q = st.number_input(
                        "Sayıyı Güncelle", value=c_q,
                        min_value=0, key=f"q_{row['id']}",
                        label_visibility="collapsed"
                    )
                    if st.button("💾 Kaydet", key=f"save_q_{row['id']}"):
                        all_db.loc[all_db['id'] == row['id'], 'soru_cozulen'] = int(n_q)
                        save_to_gsheets(all_db)
                        st.rerun()

                    st.markdown("<hr style='margin:1px 0px;'>", unsafe_allow_html=True)

                    if st.button("🌟 GÖREVİ TAMAMLA", key=f"f_{row['id']}",
                                 use_container_width=True, type="primary"):
                        for v in v_l:
                            v['done'] = False
                        all_db.loc[all_db['id'] == row['id'], 'videolar'] = json.dumps(v_l)
                        all_db.loc[all_db['id'] == row['id'], 'tamamlandi'] = True
                        save_to_gsheets(all_db)
                        st.balloons()
                        st.toast(f"Tebrikler! {row['konu']} konusunu bitirdin!", icon="🏆")
                        time.sleep(1.5)
                        st.rerun()

                    if st.button("🗑️ Planı Sil", key=f"del_act_{row['id']}",
                                 use_container_width=True):
                        save_to_gsheets(all_db[all_db['id'] != row['id']])
                        st.toast(f"{row['konu']} silindi!", icon="🗑️")
                        time.sleep(0.3)
                        st.rerun()

# ============================================================
# 12. BAŞARILARIM
# ============================================================
elif menu == "🏆 Başarılarım":
    bitenler = user_df[
        (user_df['tamamlandi'] == True) &
        (user_df['konu'] != "Hesap Aktif") &
        (user_df['ders'] != "DENEME")
    ]

    st.markdown("### 📊 Genel Başarı Tablon")
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.markdown(
            f'<div class="stat-card"><h2>🔥 {int(bitenler["soru_cozulen"].sum())}</h2>Soru Çözüldü</div>',
            unsafe_allow_html=True
        )
    with c_m2:
        st.markdown(
            f'<div class="stat-card"><h2>✅ {len(bitenler)}</h2>Konu Tamamlandı</div>',
            unsafe_allow_html=True
        )
    st.markdown("<hr style='margin:2px 0px;'>", unsafe_allow_html=True)

    for d, ikon in st.session_state.dersler.items():
        ders_df = user_df[user_df['ders'] == d]
        if not ders_df.empty:
            b_df = ders_df[ders_df['tamamlandi'] == True]
            toplam_video = sum(
                len(json.loads(r['videolar'])) if isinstance(r['videolar'], str) else 0
                for _, r in b_df.iterrows()
            )
            y = int((len(b_df) / len(ders_df)) * 100) if len(ders_df) > 0 else 0
            st.markdown(f"### {ikon} {d} (%{y})")
            st.progress(y / 100)
            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric("Biten Konu",   len(b_df))
            col_d2.metric("Toplam Soru",  int(b_df['soru_cozulen'].sum()))
            col_d3.metric("İzlenen Video", toplam_video)
            with st.expander(f"{d} Detayları"):
                for _, b in b_df.iterrows():
                    v_say = len(json.loads(b['videolar'])) if isinstance(b['videolar'], str) else 0
                    st.markdown(
                        f'<div class="success-card"><b>{b["konu"]}</b><br>'
                        f'<small>📝 {int(b["soru_cozulen"])} Soru | '
                        f'📺 {v_say} Video | 📅 {b["tarih"]}</small></div>',
                        unsafe_allow_html=True
                    )

# ============================================================
# 13. DENEME TAKİBİ
# ============================================================
elif menu == "📊 Deneme Takibi":
    st.subheader("📊 Deneme Netleri ve Puan Hesaplama")

    # FIX: user_df'ten hedef puan çek (tutarlılık için)
    hedef_puan = safe_float(
        user_df['puan_hedef'].iloc[0] if not user_df.empty and 'puan_hedef' in user_df.columns
        else 75.0,
        default=75.0
    )

    # --- Yeni Deneme Formu ---
    with st.expander("➕ Yeni Deneme Hesapla ve Kaydet", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            gk_d = st.number_input("GK Doğru",  0, 60, 0, key="new_gk_d")
            gk_y = st.number_input("GK Yanlış", 0, 60, 0, key="new_gk_y")
        with c2:
            gy_d = st.number_input("GY Doğru",  0, 60, 0, key="new_gy_d")
            gy_y = st.number_input("GY Yanlış", 0, 60, 0, key="new_gy_y")

        gk_net = gk_d - (gk_y * 0.25)
        gy_net = gy_d - (gy_y * 0.25)
        hesaplanan_puan = 40 + ((gk_net + gy_net) * 0.5)

        st.success(
            f"🧮 Netlerin: **{gk_net + gy_net:.2f}** | Tahmini Puan: **{hesaplanan_puan:.3f}**"
        )

        d_ad = st.text_input("Deneme Adı/Yayın", placeholder="Örn: Pegem TG-1")
        if st.button("🚀 Denemeyi Arşive Kaydet", use_container_width=True):
            if d_ad.strip():
                if hesaplanan_puan >= hedef_puan:
                    st.balloons()
                yeni_deneme = pd.DataFrame([{
                    "username":     username,
                    "password":     get_user_password(user_df),  # FIX: güvenli erişim
                    "display_name": d_name,
                    "ders":         "DENEME",
                    "konu":         d_ad.strip(),
                    "tarih":        str(datetime.now().date()),
                    "deneme_gk_d":  float(gk_d),
                    "deneme_gk_y":  float(gk_y),
                    "deneme_gy_d":  float(gy_d),
                    "deneme_gy_y":  float(gy_y),
                    "deneme_puan":  float(hesaplanan_puan),
                    "puan_hedef":   float(hedef_puan),
                    "tamamlandi":   True,
                    "id":           int(time.time() * 1000),
                    "videolar":     "[]",
                    "soru_cozulen": int(gk_net + gy_net),
                    "soru_hedef":   120
                }])
                save_to_gsheets(pd.concat([all_db, yeni_deneme], ignore_index=True))
                st.toast(f"✅ {d_ad} başarıyla kaydedildi!", icon="🚀")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Lütfen deneme adını giriniz!")

    st.markdown("<hr style='margin:2px 0px;'>", unsafe_allow_html=True)

    # --- Kayıtlı Denemeler ---
    st.subheader("📜 Deneme Arşivim")

    # FIX: user_df kullan, all_db filtrele değil (daha tutarlı)
    deneme_gecmisi = user_df[user_df['ders'] == "DENEME"].sort_values("id", ascending=False)

    if deneme_gecmisi.empty:
        st.info("Henüz kaydedilmiş bir deneme yok.")
    else:
        for _, d_row in deneme_gecmisi.iterrows():
            puan   = safe_float(d_row.get('deneme_puan', 0))
            h_puan = safe_float(d_row.get('puan_hedef', hedef_puan), default=hedef_puan)
            fark   = puan - h_puan

            # FIX: sütun yoksa/NaN ise 0 kullan
            gk_d_val = safe_float(d_row.get('deneme_gk_d', 0))
            gk_y_val = safe_float(d_row.get('deneme_gk_y', 0))
            gy_d_val = safe_float(d_row.get('deneme_gy_d', 0))
            gy_y_val = safe_float(d_row.get('deneme_gy_y', 0))

            if fark >= 0:
                st.success("🎉 HEDEFİNE ULAŞTIN TEBRİKLER! 🎉")
                msg   = "🔥 Mükemmel! Hedefin üzerindesin, bu iş bitti!"
                color = "#238636"
            elif fark >= -10:
                msg   = "💪 Çok yakınsın! Küçük bir gayretle hedef elinde."
                color = "#9df000"
            elif fark >= -20:
                msg   = "✍️ İşleri sıkı tut! Hedefine yaklaşıyorsun."
                color = "#ffa500"
            else:
                msg   = "🚀 Yolun başındasın, pes etme; her deneme bir basamak!"
                color = "#f85149"

            with st.container(border=True):
                col_bilgi, col_puan, col_islem = st.columns([3, 2, 1])
                with col_bilgi:
                    st.markdown(f"**{d_row['konu']}**")
                    st.caption(f"📅 {d_row['tarih']}")
                    st.write(
                        f"GK: {gk_d_val:.0f}D {gk_y_val:.0f}Y | "
                        f"GY: {gy_d_val:.0f}D {gy_y_val:.0f}Y"
                    )
                with col_puan:
                    st.markdown(f"""
                    <div style="text-align:center; display:flex; flex-direction:column;
                                align-items:center; justify-content:center; height:100%;">
                        <h2 style="margin-top:-5px; color:{color}; font-size:2.2rem;">{puan:.2f}</h2>
                        <p style="margin:0; opacity:0.6; font-size:1rem;">Hedefe Uzaklık: {fark:.2f}</p>
                        <div style="margin-top:10px;"></div>
                        <p style="font-style:italic; font-size:1.1rem;
                                  color:{color}; font-weight:500;">{msg}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_islem:
                    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_deneme_{d_row['id']}", use_container_width=True):
                        save_to_gsheets(all_db[all_db['id'] != d_row['id']])
                        st.toast("🗑️ Deneme silindi.")
                        time.sleep(0.5)
                        st.rerun()
