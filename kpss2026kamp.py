import streamlit as st
import json
import os
from collections import defaultdict
from datetime import datetime

DB_FILE = "kpss_2026_plani.json"
ADMIN_PASSWORD = st.secrets["admin_password"]

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
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 8px solid #3b82f6;
        margin-bottom: 2rem;
    }
    
    div[data-testid="stExpander"] { 
        background-color: #161B22 !important; 
        border: 1px solid #30363D !important;
        border-radius: 12px;
    }

    .history-card-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #161B22;
        opacity: 0.6;
        padding: 8px 15px;
        border-radius: 10px;
        border: 1px dashed #30363D;
        margin-bottom: 8px;
    }
    
    .stButton>button { border-radius: 8px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 3. ÜST BÖLÜM (HEADER) ---
st.markdown("""
    <div class="custom-header">
        <h1 style="margin:0; font-size: 2.2rem;">🚀 <span style="color: #3b82f6;">2026 KPSS</span> KAMPIM</h1>
        <p style="margin:0; color: #94a3b8; font-size: 1rem;">Hedefine giden yolda dijital çalışma asistanın.</p>
    </div>
    """, unsafe_allow_html=True)

menu = st.sidebar.radio("📌 ANA MENÜ", ["📅 Günlük Planım", "📝 Plan Oluştur", "🏆 Başarılarım"])

# --- 4. PLAN OLUŞTUR ---
if menu == "📝 Plan Oluştur":
    st.subheader("📝 Yeni Çalışma Planı Ekle")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            ders_secimi = st.selectbox("Ders Seçiniz", list(DERS_AYARLARI.keys()))
            konu_adi = st.text_input("Konu Adı", placeholder="Örn: Rasyonel Sayılar")
        with c2:
            tarih = st.date_input("Planlanan Tarih")
            soru_hedef = st.number_input("Hedef Soru Sayısı", min_value=0, value=50)

    st.markdown("---")
    v_sayisi = st.select_slider("Kaç adet video eklenecek?", options=list(range(1, 7)), value=1)
    
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
                    "id": len(st.session_state.data) + 1, "ders": ders_secimi, "konu": konu_adi,
                    "tarih": str(tarih), "videolar": video_listesi, "soru_hedef": int(soru_hedef),
                    "soru_cozulen": 0, "tamamlandi": False
                }
                st.session_state.data.append(yeni_girdi)
                save_data(st.session_state.data)
                st.success(f"📌 {konu_adi} başarıyla eklendi!")
                st.balloons()
                st.rerun()
            else:
                st.error("Lütfen bir konu adı giriniz!")

# --- 5. GÜNLÜK PLANIM ---
elif menu == "📅 Günlük Planım":
    col_title, col_toggle = st.columns([4, 1])
    with col_title:
        st.subheader("📅 Bugünkü Görevlerin")
    with col_toggle:
        show_history = st.toggle("📜 Geçmiş", help="Tamamlanan görevleri göster/gizle")

    aktif_gorevler = [t for t in st.session_state.data if not t['tamamlandi']]
    tamamlananlar = [t for t in st.session_state.data if t['tamamlandi']]
    
    if not aktif_gorevler:
        st.info("Harika! Aktif görevin kalmadı. Yeni planlar seni bekler.")
    else:
        plan_dict = defaultdict(list)
        for t in aktif_gorevler: plan_dict[t['tarih']].append(t)
        
        for gun in sorted(plan_dict.keys()):
            st.markdown(f"#### 🗓️ {gun}")
            for item in plan_dict[gun]:
                ikon = DERS_AYARLARI.get(item['ders'], "📌")
                with st.expander(f"{ikon} {item['ders']} - {item['konu']}", expanded=True):
                    c_left, c_right = st.columns([3, 1])
                    with c_left:
                        if item['videolar']:
                            v_cols = st.columns(2)
                            for idx, v in enumerate(item['videolar']):
                                with v_cols[idx % 2]:
                                    if not v['done']:
                                        st.video(v['url'])
                                        if st.button(f"İzledim ✅", key=f"v_{item['id']}_{idx}"):
                                            v['done'] = True
                                            save_data(st.session_state.data)
                                            st.rerun()
                                    else:
                                        st.success(f"Video {idx+1} Bitti")
                    with c_right:
                        st.markdown("**Soru Çözümü**")
                        q = st.number_input("Adet", value=item['soru_cozulen'], key=f"q_{item['id']}")
                        if q != item['soru_cozulen']:
                            item['soru_cozulen'] = q
                            save_data(st.session_state.data)
                            st.rerun()
                        
                        prog = min(item['soru_cozulen'] / item['soru_hedef'], 1.0) if item['soru_hedef'] > 0 else 0
                        st.progress(prog)
                        if st.button("🌟 BİTİR", key=f"f_{item['id']}", use_container_width=True):
                            item['tamamlandi'] = True
                            save_data(st.session_state.data)
                            st.rerun()

    if show_history:
        st.markdown("---")
        st.markdown("### 📜 Tamamlanan Görev Arşivi")
        if not tamamlananlar:
            st.caption("Henüz tamamlanmış bir görev yok.")
        else:
            hist_dict = defaultdict(list)
            for t in tamamlananlar: hist_dict[t['tarih']].append(t)
            
            for gun in sorted(hist_dict.keys(), reverse=True):
                st.markdown(f"<p style='color: #64748b; font-size: 0.8rem; margin-top:10px; margin-bottom: 5px;'>🗓️ {gun}</p>", unsafe_allow_html=True)
                for item in hist_dict[gun]:
                    hist_col_info, hist_col_btn = st.columns([5, 1.2])
                    with hist_col_info:
                        st.markdown(f"""
                            <div class="history-card-container">
                                <span><span style="color: #10b981;">✓</span> {item['ders']} - <b>{item['konu']}</b></span>
                                <span style="font-size: 0.8rem; color: #94a3b8;">{item['soru_cozulen']} Soru</span>
                            </div>
                        """, unsafe_allow_html=True)
                    with hist_col_btn:
                        if st.button("⏪ Sıfırla & Geri Al", key=f"undo_{item['id']}", help="Görevi ve videoları sıfırlayıp geri taşır"):
                            # KRİTİK GÜNCELLEME: Hem konuyu aktif yap hem de videoları sıfırla
                            item['tamamlandi'] = False
                            if 'videolar' in item:
                                for v in item['videolar']:
                                    v['done'] = False
                            save_data(st.session_state.data)
                            st.rerun()

# --- 6. BAŞARILARIM ---
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
                    st.markdown(f"<div style='border: 1px solid #3b82f6; border-radius: 10px; text-align: center; padding: 10px;'><h2 style='margin:0; color:#3b82f6;'>%{yuzde}</h2><small>BİTTİ</small></div>", unsafe_allow_html=True)
                with c2:
                    st.write(f"**İlerleme:** {len(biten)} / {len(tum)} Konu")
                    st.progress(len(biten) / len(tum))
                st.divider()
