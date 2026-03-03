import customtkinter as ctk

# --- Önceki Header Sınıfı (Aynen Kalabilir) ---
class AppHeader(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#1a1c1e", height=100, corner_radius=0, **kwargs)
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.logo_frame.pack(side="left", padx=30)
        ctk.CTkLabel(self.logo_frame, text="2026 KPSS", font=("Inter", 26, "bold"), text_color="#3b82f6").pack(side="left")
        ctk.CTkLabel(self.logo_frame, text=" KAMPIM", font=("Inter", 26), text_color="#ffffff").pack(side="left")
        
        self.info_frame = ctk.CTkFrame(self, fg_color="#2d2f31", corner_radius=12)
        self.info_frame.pack(side="right", padx=30, pady=20)
        ctk.CTkLabel(self.info_frame, text="Bugün: Genel Yetenek", font=("Inter", 13, "bold"), padx=20).pack(side="left")

# --- YENİ: Ders Kartı Bileşeni ---
class CourseCard(ctk.CTkFrame):
    def __init__(self, master, ders_adi, konu, hedef_soru, **kwargs):
        super().__init__(master, fg_color="#2d2f31", corner_radius=15, **kwargs)
        
        # Ders Başlığı
        ctk.CTkLabel(self, text=ders_adi, font=("Inter", 18, "bold"), text_color="#3b82f6").pack(anchor="w", padx=20, pady=(15, 0))
        # Konu Alt Başlığı
        ctk.CTkLabel(self, text=f"Konu: {konu}", font=("Inter", 13), text_color="#94a3b8").pack(anchor="w", padx=20)
        
        # Alt Bilgi Satırı (Soru Sayısı ve Buton)
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(footer, text=f"🎯 Hedef: {hedef_soru} Soru", font=("Inter", 12, "italic")).pack(side="left")
        ctk.CTkButton(footer, text="Tamamlandı", width=100, height=28, fg_color="#10b981", hover_color="#059669").pack(side="right")

# --- Ana Uygulama ---
root = ctk.CTk()
root.geometry("1100x750")
root.title("2026 KPSS Kamp Takip")
ctk.set_appearance_mode("dark")

# 1. Header'ı Ekle
header = AppHeader(root)
header.pack(fill="x", side="top")

# 2. Ana İçerik Alanı (Scrollable olması profesyonel gösterir)
scrollable_frame = ctk.CTkScrollableFrame(root, fg_color="transparent", label_text="Bugünkü Ders Programın", label_font=("Inter", 20, "bold"))
scrollable_frame.pack(fill="both", expand=True, padx=40, pady=20)

# 3. Örnek Verilerle Ders Kartlarını Oluştur
program_verisi = [
    ("Matematik", "Rasyonel Sayılar & Ondalık Açılım", 60),
    ("Tarih", "İslamiyet Öncesi Türk Tarihi", 40),
    ("Türkçe", "Paragrafta Yapı ve Ana Düşünce", 50),
    ("Coğrafya", "Türkiye'nin Yer Şekilleri", 30)
]

for ders, konu, soru in program_verisi:
    card = CourseCard(scrollable_frame, ders_adi=ders, konu=konu, hedef_soru=soru)
    card.pack(fill="x", pady=10)

root.mainloop()