import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings

class ClimateReporter:
    def __init__(self, data_dir, output_dir="outputs", start_year=2023, end_year=2030):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.start_year = start_year
        self.end_year = end_year
        
        # Çıktı klasörünü oluştur
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Klasör oluşturuldu: {self.output_dir}")
            
        warnings.filterwarnings("ignore")

    def _clean_dataframe(self, df):
        """Veriyi temizler ve sayısal formata çevirir."""
        df = df.set_index("Year")
        # Sayısal olmayan değerleri (örneğin '-') NaN yap ve float'a çevir
        df = df.apply(pd.to_numeric, errors='coerce')
        return df

    def process_and_plot(self, metric_config):
        """
        Tek bir metrik için veri okur, sadece ortalamayı hesaplar ve çizdirir.
        """
        file_path = os.path.join(self.data_dir, metric_config['file_name'])
        
        if not os.path.exists(file_path):
            print(f"HATA: {metric_config['file_name']} bulunamadı. Atlanıyor...")
            return

        # Veriyi yükle (ilk 5 satır metadata olduğu için skiprows=5)
        df_raw = pd.read_csv(file_path, skiprows=5)
        df_clean = self._clean_dataframe(df_raw)
        
        # Belirlenen yıl aralığını filtrele
        df_filtered = df_clean.loc[self.start_year:self.end_year]
        
        # Tüm modellerin ortalamasını hesapla
        mean_series = df_filtered.mean(axis=1)
        
        # --- Görselleştirme ---
        plt.figure(figsize=(10, 5))
        
        # SADECE Ortalama Çizgisi
        plt.plot(
            mean_series.index, 
            mean_series.values, 
            color=metric_config.get('color', 'blue'), 
            linewidth=3, 
            marker='o', # Veri noktalarını belirginleştirmek için opsiyonel
            markersize=4,
            label=f"Modeller Ortalaması"
        )

        plt.title(f"{metric_config['title']} ({self.start_year}-{self.end_year})", fontsize=14, pad=15)
        plt.xlabel("Yıl", fontsize=12)
        plt.ylabel(metric_config['unit'], fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        
        # Grafik Kaydetme
        safe_title = metric_config['title'].replace(" ", "_").lower()
        save_path = os.path.join(self.output_dir, f"{safe_title}_ortalama.png")
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        plt.close()
        
        print(f"Başarılı: {metric_config['title']} grafiği kaydedildi -> {save_path}")
        
        # İstatistiksel özeti CSV olarak kaydet
        mean_series.to_csv(os.path.join(self.output_dir, f"{safe_title}_istatistik.csv"))

# ==========================================
# VERİ TANIMLAMALARI (DIŞARIDAN DEĞİŞTİRİLEBİLİR)
# ==========================================
METRICS_LIST = [
    {
        "file_name": "pr-CMIP6_timeseries.csv",
        "title": "Yıllık Toplam Yağış",
        "unit": "mm/gün",
        "color": "blue"
    },
    {
        "file_name": "mrsos-CMIP6_timeseries.csv",
        "title": "Toprak Nemi Değişimi",
        "unit": "kg/m2",
        "color": "brown"
    }
]

# ==========================================
# ÇALIŞTIRMA
# ==========================================
if __name__ == "__main__":
    # Parametreleri burada belirleyebilirsiniz
    reporter = ClimateReporter(
        data_dir="data",                 # Verilerin olduğu klasör
        output_dir="Rapor_Sonuclari",   # Raporun kaydedileceği klasör
        start_year=2023, 
        end_year=2030
    )

    for metric in METRICS_LIST:
        reporter.process_and_plot(metric)