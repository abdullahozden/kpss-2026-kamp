import streamlit as st
import json
import os
from collections import defaultdict
from datetime import datetime

# --- 1. VERİ YÖNETİMİ ---
DB_FILE = "kpss_2026_plani.json"

# GÜVENLİK: Şifreyi Streamlit Cloud Secrets üzerinden alıyoruz
try:
    ADMIN_PASSWORD = st.secrets["admin_password"]
except:
    ADMIN_PASSWORD = "admin" # Lokal test veya Secrets ayarlanmadıysa varsayılan

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def format_yt_link(url):
    url = url.strip()
    if not url: return ""
    if not url.startswith("http"): url = "https://" + url
    return url

# --- 2. AYARLAR VE TASARIM ---
DERS_AYARLARI = {
    "Matematik": "📐", "Türkçe": "📚", "Tarih": "🏛️", "Coğrafya": "🌍", "Güncel Bilgiler": "📰"
}

st.set_page_config(page_title="2026 KPSS Kampım", layout="wide", page_icon="🎓")

# MODERN TASARIM CSS
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .custom-header {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        padding: 1.5rem; border-radius: 15px; border-left: 8px solid #3b82f6; margin-bottom: 2rem;
    }
    div[data-testid="stExpander"] { 
        background-color: #161B22 !important; border: 1px solid #30363D !important; border-radius: 12px;
    }
    .history-card-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #161B22; opacity: 0.6; padding: 8px 15px;
        border-radius: 10px; border: 1px dashed #30363D; margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# Admin oturum kontrolü
if 'is_admin_authenticated' not in st.session_state:
    st.session_state.is_admin_authenticated = False

# --- 3. ÜST BÖLÜM (HEADER) ---
st.markdown("""
    <div class="custom-header">
        <h1 style="margin:0; font-size: 2.2rem;">🚀 <span style="color: #3b82f6;">2026 KPSS</span> KAMPIM</h1>
        <p style="margin:0; color: #94a3b8; font-size: 1rem;">Admin Paneli ve Güvenli Veri Yönetimi</p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. SİDEBAR (MENÜ VE GİZLİ ADMİN) ---
st.sidebar.title("📌 ANA MENÜ")
menu = st.sidebar.radio("Sayfa Seçimi", ["📅 Günlük Planım", "📝 Plan Oluştur", "🏆 Başarılarım"], label_visibility="collapsed")

st.sidebar.markdown("---")

# SAKLI ADMİN PANELİ (Enter Desteği İçin Form Yapısında)
with st.sidebar.expander("🔐 Yönetici Girişi"):
    if not st.session_state.is_admin_authenticated:
        with st.form("admin_login_form", clear_on_submit=False):
            admin_pass_input = st.text_input("Şifre", type="password", key="admin_key")
            submit_login = st.form_submit_button("Sisteme Giriş Yap", use_container_width=True, type="primary")
            
            if submit_login:
                if admin_pass_input == ADMIN_PASSWORD:
                    st.session_state.is_admin_authenticated = True
                    st.success("Yetki Verildi! ✅")
                    st.rerun()
                else:
                    st.error("Hatalı Şifre! ❌")
    else:
        st.write("✅ Oturum Açık (Admin)")
        if st.button("Oturumu Kapat", use_container_width=True):
            st.session_state.is_admin_authenticated = False
            st.rerun()

is_admin = st.session_state.is_admin_authenticated

# --- 5. PLAN OLUŞTUR (Admin Korumalı) ---
if menu == "📝 Plan Oluştur":
    if not is_admin:
        st.warning("⚠️ **Erişim Engellendi:** Yeni plan eklemek için yönetici girişi yapmalısınız.")
    else:
        st.subheader("📝 Yeni Çalışma Planı Ekle")
        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                ders_secimi = st.selectbox("Ders Seçiniz", list(DERS_AYARLARI.keys()))
                konu_adi = st.text_input("Konu Adı")
            with c2:
                tarih = st.date_input("Planlanan Tarih")
                soru_hedef = st.number_input("Hedef Soru Sayısı", min_value=0, value=50)

        st.markdown("---")
        v_sayisi = st.select_slider("Video Sayısı", options=list(range(1, 7)), value=1)
        with st.form("video_form", clear_on_submit=True):
            video_inputlari = []
            v_cols = st.columns(2)
            for i in range(v_sayisi):
                with v_cols[i % 2]:
                    url_input = st.text_input(f"Video {i+1} URL", key=f"v_url_{i}")
                    video_inputlari.append(url_input)
            
            if st.form_submit_button("🔥 Programıma Kaydet"):
                if konu_adi:
                    video_listesi = [{"url": format_yt_link(u), "done": False} for u in video_inputlari if u.strip()]
                    yeni_girdi = {
                        "id": int(datetime.now().timestamp() * 1000), # Benzersiz ID üretimi
                        "ders": ders_secimi, "konu": konu_adi,
                        "tarih": str(tarih), "videolar": video_listesi, "soru_hedef": int(soru_hedef),
                        "soru_cozulen": 0, "tamamlandi": False
                    }
                    st.session_state.data.append(yeni_girdi)
                    save_data(st.session_state.data)
                    st.success("📌 Plan başarıyla kaydedildi!")
                    st.rerun()

# --- 6. GÜNLÜK PLANIM ---
elif menu == "📅 Günlük Planım":
    col_t, col_tog = st.columns([4, 1])
    with col_t: st.subheader("📅 Bugünkü Görevlerin")
    with col_tog: show_history = st.toggle("📜 Geçmiş")

    aktif = [t for t in st.session_state.data if not t['tamamlandi']]
    tamamlananlar = [t for t in st.session_state.data if t['tamamlandi']]
    
    if not aktif:
        st.info("Yapılacak aktif bir görev yok. Yeni planlar ekleyebilirsin!")
    else:
        plan_dict = defaultdict(list)
        for t in aktif: plan_dict[t['tarih']].append(t)
        for gun in sorted(plan_dict.keys()):
            st.markdown(f"#### 🗓️ {gun}")
            for item in plan_dict[gun]:
                ikon = DERS_AYARLARI.get(item['ders'], "📌")
                with st.expander(f"{ikon} {item['ders']} - {item['konu']}", expanded=True):
                    c_l, c_r = st.columns([3, 1])
                    with c_l:
                        if item['videolar']:
                            v_c = st.columns(2)
                            for idx, v in enumerate(item['videolar']):
                                with v_c[idx % 2]:
                                    if not v['done']:
                                        st.video(v['url'])
                                        if st.button(f"İzledim ✅", key=f"v_{item['id']}_{idx}"):
                                            v['done'] = True
                                            save_data(st.session_state.data)
                                            st.rerun()
                                    else: st.success(f"Video {idx+1} Bitti")
                    with c_r:
                        st.markdown("**Soru Çözümü**")
                        yeni_q = st.number_input("Adet", value=item['soru_cozulen'], key=f"q_{item['id']}")
                        if yeni_q != item['soru_cozulen']:
                            item['soru_cozulen'] = yeni_q
                            save_data(st.session_state.data)
                            st.rerun()
                        
                        prog = min(item['soru_cozulen'] / item['soru_hedef'], 1.0) if item['soru_hedef'] > 0 else 0
                        st.progress(prog)
                        
                        # --- AKSİYON BUTONLARI ---
                        if st.button("🌟 BİTİR", key=f"f_{item['id']}", use_container_width=True, type="primary"):
                            item['tamamlandi'] = True
                            save_data(st.session_state.data)
                            st.balloons()
                            st.rerun()
                        
                        # KRİTİK EKLENTİ: Sadece Admin Silebilir
                        if is_admin:
                            st.write("") # Boşluk
                            if st.button("🗑️ PLANI SİL", key=f"del_{item['id']}", use_container_width=True):
                                st.session_state.data = [x for x in st.session_state.data if x['id'] != item['id']]
                                save_data(st.session_state.data)
                                st.rerun()

    if show_history:
        st.markdown("---")
        st.markdown("### 📜 Tamamlanan Görev Arşivi")
        if not tamamlananlar: st.caption("Henüz tamamlanmış görev yok.")
        else:
            hist_dict = defaultdict(list)
            for t in tamamlananlar: hist_dict[t['tarih']].append(t)
            for gun in sorted(hist_dict.keys(), reverse=True):
                st.markdown(f"<small style='color:#64748b;'>🗓️ {gun}</small>", unsafe_allow_html=True)
                for item in hist_dict[gun]:
                    h_info, h_btn = st.columns([5, 1.2])
                    with h_info:
                        st.markdown(f"""<div class="history-card-container"><span>✓ {item['ders']} - <b>{item['konu']}</b></span><span>{item['soru_cozulen']} Soru</span></div>""", unsafe_allow_html=True)
                    with h_btn:
                        if is_admin:
                            if st.button("⏪ Geri Al", key=f"un_{item['id']}"):
                                item['tamamlandi'] = False
                                for v in item.get('videolar', []): v['done'] = False
                                save_data(st.session_state.data)
                                st.rerun()

# --- 7. BAŞARILARIM ---
elif menu == "🏆 Başarılarım":
    st.subheader("🏆 Gelişim Raporu")
    if not st.session_state.data:
        st.warning("Veri bulunamadı.")
    else:
        for d, ikon in DERS_AYARLARI.items():
            tum = [t for t in st.session_state.data if t['ders'] == d]
            biten = [t for t in tum if t['tamamlandi']]
            if tum:
                yuzde = int((len(biten) / len(tum)) * 100)
                st.markdown(f"### {ikon} {d}")
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.metric("Bitti", f"%{yuzde}")
                with c2:
                    st.write(f"İlerleme: {len(biten)} / {len(tum)} Konu")
                    st.progress(len(biten) / len(tum))
                st.divider()
