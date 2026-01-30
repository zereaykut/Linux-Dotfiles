import os
import json
import requests
import xarray as xr
from datetime import datetime, timedelta

# -------------------------------------------------------------------------
# AYARLAR
# -------------------------------------------------------------------------

# İndirilecek Tarih ve Model Saati (Run)
DATE = datetime.utcnow().strftime("%Y%m%d") # Bugün (örn: 20241130)
RUN = "00"  # Seçenekler: "00", "06", "12", "18"

# İndirilecek Tahmin Adımları (Saat bazında: 0, 3, 6 ...)
STEPS = [0, 3, 6] 

# İstenen Değişkenler (Swift dosyasındaki 'param' veya 'shortName' karşılıkları)
# 2t: 2m Temperature, tp: Total Precipitation, msl: Mean Sea Level Pressure
TARGET_PARAMS = ["2t", "tp", "msl"]

# Türkiye Sınırları (Bounding Box)
TURKEY_AREA = {
    "north": 42.5,
    "south": 35.5,
    "west": 25.5,
    "east": 45.0
}

# Kayıt Klasörü
OUTPUT_DIR = "./ecmwf_turkey_data"
BASE_URL = "https://data.ecmwf.int/forecasts"

# -------------------------------------------------------------------------
# MANTIK (Swift Kodundan Uyarlama)
# -------------------------------------------------------------------------

def get_product_type(run_hour):
    """
    EcmwfDomain.swift içerisindeki mantığa göre ürün tipi belirleme.
    00 ve 12 -> 'oper'
    06 ve 18 -> 'scda'
    """
    if run_hour in ["00", "12"]:
        return "oper"
    return "scda"

def generate_base_url(date, run):
    """
    URL yapısını oluşturur.
    Örn: https://data.ecmwf.int/forecasts/20250101/00z/ifs/0p25/oper/
    """
    product = get_product_type(run)
    # IFS High Resolution (0.25 derece) kullanıyoruz (ifs025)
    return f"{BASE_URL}/{date}/{run}z/ifs/0p25/{product}"

def download_file_partial(url, target_params, output_path):
    """
    Swift kodundaki 'downloadEcmwfIndexed' fonksiyonunun Python karşılığı.
    Önce .index dosyasını indirir, byte aralıklarını bulur ve sadece o kısımları indirir.
    """
    index_url = url + ".index"
    print(f"Index indiriliyor: {index_url}")
    
    try:
        r_index = requests.get(index_url)
        r_index.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"HATA: Index dosyası bulunamadı. Veri henüz yayınlanmamış olabilir: {index_url}")
        return False

    # Byte aralıklarını topla
    byte_ranges = []
    found_params = []
    
    # Index dosyası JSON Lines formatındadır
    for line in r_index.text.splitlines():
        try:
            entry = json.loads(line)
            # Parametre kontrolü (Swift kodundaki filter mantığı)
            if entry.get("param") in target_params:
                offset = entry.get("_offset")
                length = entry.get("_length")
                if offset is not None and length is not None:
                    byte_ranges.append((offset, offset + length - 1))
                    found_params.append(entry.get("param"))
        except json.JSONDecodeError:
            continue

    if not byte_ranges:
        print("İstenen parametreler index dosyasında bulunamadı.")
        return False

    print(f"Bulunan parametreler: {set(found_params)}. İndirme başlıyor...")

    # Byte aralıklarını birleştir ve indir
    # Basitlik olması için her aralığı ayrı ayrı indirip dosyaya ekleyeceğiz.
    # (Swift kodu concurrent indirme yapıyor, burada sequential yapıyoruz)
    
    with open(output_path, "wb") as f_out:
        for start, end in byte_ranges:
            headers = {"Range": f"bytes={start}-{end}"}
            r_data = requests.get(url, headers=headers, stream=True)
            if r_data.status_code == 206: # Partial Content
                for chunk in r_data.iter_content(chunk_size=8192):
                    f_out.write(chunk)
            else:
                print(f"Range request başarısız oldu: {r_data.status_code}")
    
    return True

def crop_to_turkey(input_path, output_path):
    """
    İndirilen global veya parçalı veriyi xarray ile açıp Türkiye koordinatlarına göre keser.
    """
    try:
        # GRIB dosyasını aç (cfgrib motoru ile)
        ds = xr.open_dataset(input_path, engine='cfgrib')
        
        # Koordinatları kes (ECMWF verisi genellikle lat 90 to -90, lon 0 to 360 formatındadır)
        # Türkiye Lon: 25.5 - 45.0, Lat: 42.5 - 35.5
        
        # Grib dosyalarında boylam bazen 0-360, bazen -180/180 olabilir. Kontrol edelim.
        # Genelde 0-360 gelir.
        
        ds_turkey = ds.sel(
            latitude=slice(TURKEY_AREA["north"], TURKEY_AREA["south"]), # Kuzeyden güneye azalıyor olabilir
            longitude=slice(TURKEY_AREA["west"], TURKEY_AREA["east"])
        )
        
        print(f"Türkiye verisi kesiliyor ve kaydediliyor: {output_path}")
        # NetCDF olarak kaydetmek daha hızlı ve okuması kolaydır
        ds_turkey.to_netcdf(output_path)
        ds.close()
        
        # Geçici indirilen ham dosyayı sil (isteğe bağlı)
        os.remove(input_path)
        
    except Exception as e:
        print(f"Kesme işlemi sırasında hata (eccodes kurulu mu?): {e}")

# -------------------------------------------------------------------------
# ÇALIŞTIRMA
# -------------------------------------------------------------------------

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    base_path = generate_base_url(DATE, RUN)
    product = get_product_type(RUN)

    for step in STEPS:
        # Dosya adı formatı: 20250101000000-0h-oper-fc.grib2
        # Tarih + Run + 0000
        filename_prefix = f"{DATE}{RUN}0000"
        filename = f"{filename_prefix}-{step}h-{product}-fc.grib2"
        
        full_url = f"{base_path}/{filename}"
        
        temp_grib_path = os.path.join(OUTPUT_DIR, f"temp_global_{step}h.grib2")
        final_nc_path = os.path.join(OUTPUT_DIR, f"ecmwf_turkey_{DATE}_{RUN}z_{step}h.nc")
        
        print(f"--- İşleniyor: {step}. saat ---")
        
        # 1. Kısmi İndirme (Swift mantığı)
        success = download_file_partial(full_url, TARGET_PARAMS, temp_grib_path)
        
        # 2. Türkiye Bölgesini Kesme (Domain filter)
        if success:
            crop_to_turkey(temp_grib_path, final_nc_path)
            print("Tamamlandı.\n")