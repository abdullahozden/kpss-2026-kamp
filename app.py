import streamlit as st
import json
import os
from collections import defaultdict
from datetime import datetime

# --- 1. VERİ YÖNETİMİ ---
DB_FILE = "kpss_2026_plani.json"

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

# MODERN DARK THEME CSS (Cilalı Görünüm)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Profesyonel Header Alanı */
    .custom-header {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 8px solid #3b82f6;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Kart Tasarımları */
    div[data-testid="stExpander"] { 
        background-color: #161B22 !important; 
        border: 1px solid #30363D !important;
        border-radius: 12px;
        margin-bottom: 10px;
    }
    
    .stButton>button { 
        border-radius: 8px; 
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .topic-card { 
        background-color: #1c2128; 
        padding: 15px; 
        border-radius: 10px; 
        margin-top: 8px; 
        border-left: 5px solid #10b981; 
    }
    
    .metric-box { 
        background-color: #161B22; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #3b82f6; 
        text-align: center; 
    }
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
        c_info1, c_info2 = st.columns(2)
        with c_info1:
            ders_secimi = st.selectbox("Ders Seçiniz", list(DERS_AYARLARI.keys()))
            konu_adi_girdisi = st.text_input("Konu Adı", placeholder="Örn: Paragrafta Anlam")
        with c_info2:
            tarih_girdisi = st.date_input("Planlanan Tarih")
            soru_hedef_girdisi = st.number_input("Hedef Soru Sayısı", min_value=0, value=50)

    st.markdown("---")
    st.write("📺 **Video Kaynakları**")
    v_sayisi = st.select_slider("Kaç adet video ekleyeceksin?", options=list(range(1, 7)), value=1)
    
    with st.form("video_form", clear_on_submit=True):
        video_inputlari = []
        v_cols = st.columns(2)
        for i in range(v_sayisi):
            with v_cols[i % 2]:
                url_input = st.text_input(f"Video {i+1} URL", key=f"v_url_{i}")
                video_inputlari.append(url_input)
        
        submit_button = st.form_submit_button("🔥 Programıma Kaydet")
        
        if submit_button:
            if konu_adi_girdisi:
                video_listesi = [{"url": format_yt_link(u), "done": False} for u in video_inputlari if u.strip()]
                yeni_girdi = {
                    "id": len(st.session_state.data) + 1, "ders": ders_secimi, "konu": konu_adi_girdisi,
                    "tarih": str(tarih_girdisi), "videolar": video_listesi, "soru_hedef": int(soru_hedef_girdisi),
                    "soru_cozulen": 0, "tamamlandi": False
                }
                st.session_state.data.append(yeni_girdi)
                save_data(st.session_state.data)
                st.success(f"📌 {konu_adi_girdisi} listeye eklendi!")
                st.balloons()
            else:
                st.error("Lütfen bir konu adı giriniz!")

# --- 5. GÜNLÜK PLANIM ---
elif menu == "📅 Günlük Planım":
    aktif_gorevler = [t for t in st.session_state.data if not t['tamamlandi']]
    
    if not aktif_gorevler:
        st.info("Tamamlanacak görev kalmadı! 'Plan Oluştur' kısmından yeni konular ekleyebilirsin.")
    else:
        günlük_plan = defaultdict(list)
        for t in aktif_gorevler: günlük_plan[t['tarih']].append(t)
        
        for gun in sorted(günlük_plan.keys()):
            st.markdown(f"#### 🗓️ {gun}")
            for item in günlük_plan[gun]:
                ikon = DERS_AYARLARI.get(item['ders'], "📌")
                with st.expander(f"{ikon} {item['ders']} - {item['konu']}", expanded=True):
                    col_left, col_right = st.columns([3, 1]) 
                    
                    with col_left:
                        if item['videolar']:
                            v_grid_cols = st.columns(2)
                            for idx, v in enumerate(item['videolar']):
                                with v_grid_cols[idx % 2]:
                                    if not v['done']:
                                        st.video(v['url'])
                                        if st.button(f"İzledim ✅", key=f"v_btn_{item['id']}_{idx}"):
                                            v['done'] = True
                                            save_data(st.session_state.data)
                                            st.rerun()
                                    else:
                                        st.success(f"Video {idx+1} Bitti")
                    
                    with col_right:
                        st.markdown("**✍️ Soru Çözümü**")
                        yeni_q = st.number_input("Adet", value=item['soru_cozulen'], key=f"q_{item['id']}")
                        if yeni_q != item['soru_cozulen']:
                            item['soru_cozulen'] = yeni_q
                            save_data(st.session_state.data)
                            st.rerun()
                        
                        prog = min(item['soru_cozulen'] / item['soru_hedef'], 1.0) if item['soru_hedef'] > 0 else 0
                        st.progress(prog)
                        st.caption(f"%{int(prog*100)} tamamlandı")
                        
                        if st.button("🌟 BİTİR", key=f"fin_{item['id']}", use_container_width=True):
                            item['tamamlandi'] = True
                            save_data(st.session_state.data)
                            st.rerun()

# --- 6. BAŞARILARIM ---
elif menu == "🏆 Başarılarım":
    st.subheader("🏆 Gelişim Raporu")
    
    if not st.session_state.data:
        st.warning("Henüz veri girişi yapılmamış.")
    else:
        for d, ikon in DERS_AYARLARI.items():
            tum_konular = [t for t in st.session_state.data if t['ders'] == d]
            biten_konular = [t for t in tum_konular if t['tamamlandi']]
            
            if tum_konular:
                yüzde = int((len(biten_konular) / len(tum_konular)) * 100)
                st.markdown(f"### {ikon} {d}")
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.markdown(f"<div class='metric-box'><h2 style='margin:0; color:#3b82f6;'>%{yüzde}</h2><small>BİTTİ</small></div>", unsafe_allow_html=True)
                with c2:
                    st.write(f"**İlerleme:** {len(biten_konular)} / {len(tum_konular)} Konu")
                    st.progress(len(biten_konular) / len(tum_konular))
                
                if biten_konular:
                    with st.expander(f"📚 {d} Arşivi"):
                        for topic in biten_konular:
                            st.markdown(f"<div class='topic-card'><b>📌 {topic['konu']}</b><br><small>📅 {topic['tarih']} | ✍️ {topic['soru_cozulen']} Soru</small></div>", unsafe_allow_html=True)
                st.divider()
