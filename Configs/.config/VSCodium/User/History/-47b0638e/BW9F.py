import os
import json
import requests
import numpy as np
import xarray as xr
import pandas as pd
from datetime import datetime, timedelta

# -------------------------------------------------------------------------
# 1. AYARLAR
# -------------------------------------------------------------------------
DATE = datetime.utcnow().strftime("%Y%m%d") # Örn: 20241201
RUN = "00"  # 00 veya 12 UTC
STEPS = [0, 3, 6, 9, 12] # 3 saatlik adımları indiriyoruz

# İstenen Değişkenler (ECMWF Kısa Adları)
# 2t: Sıcaklık, tcc: Toplam Bulutluluk, 10u/10v: Rüzgar Bileşenleri, ssrd: Radyasyon
TARGET_PARAMS = ["2t", "tcc", "10u", "10v", "ssrd"]

TURKEY_AREA = {"north": 42.5, "south": 35.5, "west": 25.5, "east": 45.0}
OUTPUT_DIR = "./ecmwf_hourly_processing"
BASE_URL = "https://data.ecmwf.int/forecasts"

# -------------------------------------------------------------------------
# 2. İNDİRME FONKSİYONLARI (Önceki mantıkla aynı)
# -------------------------------------------------------------------------
def get_url(date, run, step):
    product = "oper" if run in ["00", "12"] else "scda"
    # Dosya adı örn: 20241201000000-3h-oper-fc.grib2
    filename = f"{date}{run}0000-{step}h-{product}-fc.grib2"
    return f"{BASE_URL}/{date}/{run}z/ifs/0p25/{product}/{filename}"

def download_partial(url, params, path):
    """Index dosyasını kullanarak sadece gerekli parametreleri indirir."""
    if os.path.exists(path): return True
    try:
        idx = requests.get(url + ".index").text.splitlines()
        ranges = []
        for line in idx:
            entry = json.loads(line)
            if entry.get("param") in params:
                ranges.append((entry["_offset"], entry["_offset"] + entry["_length"] - 1))
        
        with open(path, "wb") as f:
            for start, end in ranges:
                headers = {"Range": f"bytes={start}-{end}"}
                f.write(requests.get(url, headers=headers).content)
        return True
    except Exception as e:
        print(f"İndirme hatası: {e}")
        return False

# -------------------------------------------------------------------------
# 3. İŞLEME VE SAATLİĞE ÇEVİRME (CORE LOGIC)
# -------------------------------------------------------------------------

def process_data():
    files = []
    print(f"--- {DATE} {RUN}z İndirme Başlıyor ---")
    
    # 1. Adım: Tüm dosyaları indir
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    for step in STEPS:
        url = get_url(DATE, RUN, step)
        local_path = f"{OUTPUT_DIR}/raw_{step}h.grib2"
        if download_partial(url, TARGET_PARAMS, local_path):
            files.append(local_path)
            print(f"İndirildi: {step}. saat")

    print("\n--- Veri İşleniyor ve Saatliğe Dönüştürülüyor ---")

    # 2. Adım: Dosyaları xarray ile birleştir (Time ekseninde)
    # step tipi 'accum' olan radyasyon (ssrd) ile 'instant' olanlar (2t) bazen çakışır.
    # Bu yüzden filter_by_keys ile ayırıp birleştirmek en sağlıklısıdır.
    
    datasets = []
    for f in files:
        # cfgrib bazen farklı değişken tiplerini ayrı dataset olarak açar
        try:
            ds = xr.open_dataset(f, engine="cfgrib", backend_kwargs={'filter_by_keys': {'stepType': 'instant'}})
            ds_acc = xr.open_dataset(f, engine="cfgrib", backend_kwargs={'filter_by_keys': {'stepType': 'accum'}})
            ds = xr.merge([ds, ds_acc], compat='override')
        except:
            # Sadece instant veya sadece accum varsa
            ds = xr.open_dataset(f, engine="cfgrib")
        
        # Türkiye kesmesi
        ds = ds.sel(latitude=slice(TURKEY_AREA["north"], TURKEY_AREA["south"]), 
                    longitude=slice(TURKEY_AREA["west"], TURKEY_AREA["east"]))
        datasets.append(ds)

    # Zaman ekseninde birleştir
    full_ds = xr.concat(datasets, dim="step")

    # Geçerli zaman (valid_time) indeksini oluştur
    # step değerlerini (nanosecond) saate çevirip run time'a ekliyoruz
    valid_times = [datetime.strptime(f"{DATE}{RUN}", "%Y%m%d%H") + timedelta(hours=int(s)) for s in STEPS]
    full_ds = full_ds.assign_coords(valid_time=("step", valid_times))
    full_ds = full_ds.swap_dims({"step": "valid_time"})

    # ---------------------------------------------------------------------
    # 4. INTERPOLASYON (1 SAATLİK ÇÖZÜNÜRLÜK)
    # ---------------------------------------------------------------------
    
    # Yeni saatlik zaman ekseni (Örn: 00:00, 01:00, 02:00...)
    hourly_times = pd.date_range(start=valid_times[0], end=valid_times[-1], freq="1h")
    
    # A. Lineer Değişkenler (Sıcaklık, Bulutluluk, Rüzgar Bileşenleri)
    # Cubic spline (hermite benzeri) kullanarak yumuşak geçiş sağlarız.
    ds_hourly = full_ds[['t2m', 'tcc', 'u10', 'v10']].interp(valid_time=hourly_times, method="cubic")

    # B. Rüzgar Hızı ve Yönü Hesaplama (Bileşenlerden)
    # Open-Meteo EcmwfReader.swift satır 146-150: u ve v'den hız hesaplanır.
    ds_hourly['wind_speed'] = np.sqrt(ds_hourly['u10']**2 + ds_hourly['v10']**2)
    
    # Rüzgar Yönü (Derece)
    # atan2 sonucu radyandır, dereceye çevrilir. (Met. convention: rüzgarın geldiği yön)
    ds_hourly['wind_direction'] = (np.degrees(np.arctan2(ds_hourly['u10'], ds_hourly['v10'])) + 360) % 360

    # C. Radyasyon (Zor Kısım: De-accumulation)
    # ECMWF'de radyasyon (ssrd), tahmin başlangıcından itibaren birikir (Joule/m2).
    # 1. Önce birikimli veriyi saatliğe interpolate et (monoton artan bir eğri olur).
    ds_rad_interp = full_ds['ssrd'].interp(valid_time=hourly_times, method="linear")
    
    # 2. Saatlik farkı al (Joule/hour)
    # İlk saat (00:00) 0 kabul edilir veya NaN olur, 0 ile doldururuz.
    rad_diff = ds_rad_interp.diff(dim="valid_time", label="upper")
    
    # Başlangıçtaki eksik saati doldurmak için (reindex veya fillna)
    rad_diff = rad_diff.reindex(valid_time=hourly_times).fillna(0)
    
    # 3. Birim Dönüşümü: Joule/m² -> Watt/m²
    # 1 saat = 3600 saniye. Watt = Joule / Saniye
    ds_hourly['shortwave_radiation'] = rad_diff / 3600.0
    
    # Negatif değerleri temizle (interpolasyon hatası veya gece oluşabilir)
    ds_hourly['shortwave_radiation'] = ds_hourly['shortwave_radiation'].where(ds_hourly['shortwave_radiation'] > 0, 0)

    # ---------------------------------------------------------------------
    # 5. KAYIT
    # ---------------------------------------------------------------------
    output_nc = f"{OUTPUT_DIR}/turkey_hourly_{DATE}.nc"
    ds_hourly.to_netcdf(output_nc)
    print(f"Başarılı! Dosya kaydedildi: {output_nc}")
    print("İçerik:", list(ds_hourly.data_vars))

if __name__ == "__main__":
    process_data()