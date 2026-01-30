from datetime import date
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings

class ClimateReporter:
    def __init__(self, data_dir, output_dir="outputs", start_year=date.today().year - 2, end_year=date.today().year + 5):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.start_year = start_year
        self.end_year = end_year
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Klasör oluşturuldu: {self.output_dir}")
            
        warnings.filterwarnings("ignore")

    def _clean_dataframe(self, df):
        df = df.set_index("Year")
        df = df.apply(pd.to_numeric, errors="coerce")
        return df

    def process_and_plot(self, metric_config):
        file_path = os.path.join(self.data_dir, metric_config["file_name"])
        
        if not os.path.exists(file_path):
            print(f"HATA: {metric_config["file_name"]} bulunamadı. Atlanıyor...")
            return

        df_raw = pd.read_csv(file_path, skiprows=5)
        df_clean = self._clean_dataframe(df_raw)
        df_filtered = df_clean.loc[self.start_year:self.end_year]
        
        # --- İstatistiksel Hesaplamalar ---
        mean_series = df_filtered.mean(axis=1)
        min_series = df_filtered.min(axis=1) # Modeller arası en düşük değer
        max_series = df_filtered.max(axis=1) # Modeller arası en yüksek değer
        
        # --- Görselleştirme ---
        plt.figure(figsize=(12, 6))
        
        # 1. Gölgeli Alan (Model Yayılımı / Uncertainty Range)
        plt.fill_between(
            df_filtered.index, 
            min_series, 
            max_series, 
            color=metric_config.get("color", "blue"), 
            alpha=0.15, 
            label="Model Yayılımı (Min-Max)"
        )
        
        # 2. Bireysel Model Çizgileri (Arka Plan)
        for col in df_filtered.columns:
            plt.plot(df_filtered.index, df_filtered[col], color="gray", alpha=0.5, linewidth=0.5)
            
        # 3. Ortalama Çizgisi (Ön Plan)
        plt.plot(
            mean_series.index, 
            mean_series.values, 
            color=metric_config.get("color", "blue"), 
            linewidth=3, 
            label=f"Modeller Ortalaması"
        )

        # Grafik Detayları
        plt.title(f"{metric_config["title"]} ({self.start_year}-{self.end_year})", fontsize=14, pad=15)
        plt.xlabel("Yıl", fontsize=12)
        plt.ylabel(metric_config["unit"], fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(loc="upper left", frameon=True)
        
        # Kaydetme
        safe_title = metric_config["title"].replace(" ", "_").lower()
        save_path = os.path.join(self.output_dir, f"{safe_title}_plot.png")
        plt.savefig(save_path, bbox_inches="tight", dpi=150)
        plt.close()


        # --- Görselleştirme ---
        plt.figure(figsize=(10, 5))

        # SADECE Ortalama Çizgisi
        plt.plot(
            mean_series.index, 
            mean_series.values, 
            color=metric_config.get("color", "blue"), 
            linewidth=3, 
            marker="o", # Veri noktalarını belirginleştirmek için opsiyonel
            markersize=4,
            label=f"Modeller Ortalaması"
        )

        plt.title(f"{metric_config["title"]} ({self.start_year}-{self.end_year})", fontsize=14, pad=15)
        plt.xlabel("Yıl", fontsize=12)
        plt.ylabel(metric_config["unit"], fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        
        # Grafik Kaydetme
        safe_title = metric_config["title"].replace(" ", "_").lower()
        save_path = os.path.join(self.output_dir, f"{safe_title}_ortalama.png")
        plt.savefig(save_path, bbox_inches="tight", dpi=150)
        plt.close()

        print(f"Başarılı: {metric_config["title"]} analizi tamamlandı.")
        
        # Verileri de CSV olarak kaydet (opsiyonel)
        stats_df = pd.DataFrame({
            "Mean": mean_series,
            "Min": min_series,
            "Max": max_series
        })
        stats_df.to_csv(os.path.join(self.output_dir, f"{safe_title}_stats.csv"))

# ==========================================
# VERİ TANIMLAMALARI (DIŞARIDAN VERİLEBİLİR)
# ==========================================
METRICS_LIST = [
    {
        "file_name": "pr-CMIP6_timeseries.csv",
        "title": "Yıllık Toplam Yağış",
        "unit": "mm/gün",
        "color": "#1f77b4" # Profesyonel mavi tonu
    },
    {
        "file_name": "mrsos-CMIP6_timeseries.csv",
        "title": "Toprak Nemi Değişimi",
        "unit": "kg/m2",
        "color": "#8c564b" # Toprak tonu kahverengi
    },
    {
        "file_name": "prsn-CMIP5_timeseries.csv",
        "title": "Toprak Nemi Değişimi",
        "unit": "kg/m2",
        "color": "#8c564b" # Toprak tonu kahverengi
    }
]

# ==========================================
# ÇALIŞTIRMA
# ==========================================
if __name__ == "__main__":
    # Verilerin bulunduğu yol (".", dosyalar kodla aynı yerdeyse kullanılır)
    DATA_PATH = "data" 
    
    reporter = ClimateReporter(
        data_dir=DATA_PATH, 
        output_dir="Rapor_Sonuclari", 
        start_year=2023, 
        end_year=2030
    )

    for metric in METRICS_LIST:
        reporter.process_and_plot(metric)