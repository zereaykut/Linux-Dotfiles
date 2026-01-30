#!/usr/bin/env python
"""
MeteoFrance ARPEGE GRIB paket indirme script'i (Open-Meteo Swift kodundan uyarlanmıştır).

- Domain: arpege_europe veya arpege_world
- Paketler: SP1, SP2, HP1, IP1 (yüzey + basınç seviyeleri)
- Kaynak: object.data.gouv.fr (gov server), isteğe bağlı olarak MeteoFrance API de eklenebilir.

Swift referansı:
- MeteoFranceDomain.mfApiPackageTimes, mfApiPackagesSurface, mfApiPackagesPressure
- MeteoFranceDownload.download3(...)
"""

import argparse
import datetime as dt
import os
from pathlib import Path

import requests


# Kullanım

# python arpage.py \
#     --domain arpege_world \
#     --run 2024-06-23T00 \
#     --output ./data/arpege_world \
#     --use-gov-server

DOMAINS = {
    "arpege_europe": {
        "family": "arpege",   # Swift'teki domain.family.rawValue :contentReference[oaicite:3]{index=3}
        "grid_api": "0.1",    # mfApiGridName
        "grid_res": "01",     # gov server path (0.1 -> 01)
        "package_times": [    # mfApiPackageTimes for arpege_europe :contentReference[oaicite:4]{index=4}
            "000H012H", "013H024H", "025H036H", "037H048H",
            "049H060H", "061H072H", "073H084H", "085H096H", "097H102H"
        ],
        "packages_surface": ["SP1", "SP2", "HP1"],  # mfApiPackagesSurface
        "packages_pressure": ["IP1"],               # mfApiPackagesPressure
        "update_interval_hours": 6,
    },
    "arpege_world": {
        "family": "arpege",
        "grid_api": "0.25",
        "grid_res": "025",
        "package_times": [
            "000H024H", "025H048H", "049H072H", "073H102H"
        ],
        "packages_surface": ["SP1", "SP2", "HP1"],
        "packages_pressure": ["IP1"],
        "update_interval_hours": 6,
    },
}


def guess_last_run(domain: str) -> dt.datetime:
    """
    Swift kodundaki lastRun mantığını taklit eder:
      t = now - 2h
      floor(toNearestHour: 6)  (ARPEGE için) :contentReference[oaicite:5]{index=5}
    """
    info = DOMAINS[domain]
    interval = info["update_interval_hours"]
    now = dt.datetime.utcnow()
    t = now - dt.timedelta(hours=2)

    floored_hour = (t.hour // interval) * interval
    run = t.replace(hour=floored_hour, minute=0, second=0, microsecond=0)
    return run


def parse_run(run_str: str) -> dt.datetime:
    """
    Çeşitli formatları dene:
    - 2024-06-23T00
    - 2024062300
    - 2024-06-23T00:00
    """
    for fmt in ("%Y-%m-%dT%H", "%Y%m%d%H", "%Y-%m-%dT%H:%M"):
        try:
            return dt.datetime.strptime(run_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Run formatı anlaşılamadı: {run_str}")


def build_gov_url(domain: str, run: dt.datetime, package: str, package_time: str) -> str:
    """
    Swift'teki URL yapısına bire bir yakın: :contentReference[oaicite:6]{index=6}

    https://object.data.gouv.fr/meteofrance-pnt/pnt/{run_iso}:00Z/{family}/{gridRes}/{package}/
        {family}__{gridRes}__{package}__{packageTime}__{run_iso}:00Z.grib2
    """
    info = DOMAINS[domain]
    family = info["family"]  # "arpege"
    grid_res = info["grid_res"]  # "01" veya "025"

    run_iso_short = run.strftime("%Y-%m-%dT%H:%M")  # Swift: iso8601_YYYY_MM_dd_HH_mm

    path_prefix = f"{run_iso_short}:00Z/{family}/{grid_res}/{package}"
    filename = f"{family}__{grid_res}__{package}__{package_time}__{run_iso_short}:00Z.grib2"

    url = f"https://object.data.gouv.fr/meteofrance-pnt/pnt/{path_prefix}/{filename}"
    return url


def download_file(url: str, out_path: Path, timeout: int = 600) -> bool:
    """
    Tek bir URL'yi indir ve diske yaz. 200 harici durumda False döndür.
    """
    print(f"[INFO] Downloading: {url}")
    resp = requests.get(url, timeout=timeout, stream=True)

    if resp.status_code != 200:
        print(f"[WARN] HTTP {resp.status_code} for {url}")
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")

    with open(tmp_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    tmp_path.replace(out_path)
    print(f"[OK] Saved to {out_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="MeteoFrance ARPEGE GRIB paket downloader (Python port)"
    )
    parser.add_argument(
        "--domain",
        required=True,
        choices=list(DOMAINS.keys()),
        help="Model domain: arpege_europe veya arpege_world",
    )
    parser.add_argument(
        "--run",
        help="Koşum saati. Örn: 2024-06-23T00 veya 2024062300. Boşsa otomatik tahmin edilir.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="İndirilen GRIB dosyalarının kaydedileceği klasör",
    )
    parser.add_argument(
        "--max-forecast-hour",
        type=int,
        default=None,
        help="Belirtilirse, package_time başlangıç saati bu değerden büyük olanlar atlanır (örn. 72).",
    )
    parser.add_argument(
        "--packages",
        help="Virgülle ayrılmış paket listesi (SP1,SP2,HP1,IP1). Boş ise surface+pressure hepsi.",
    )
    parser.add_argument(
        "--use-gov-server",
        action="store_true",
        help="Gov server (object.data.gouv.fr) kullan. (Default zaten bu script'te)",
    )

    args = parser.parse_args()

    if args.domain not in DOMAINS:
        raise SystemExit(f"Desteklenmeyen domain: {args.domain}")

    if args.run:
        run = parse_run(args.run)
    else:
        run = guess_last_run(args.domain)
        print(f"[INFO] Run belirtilmedi, tahmin edilen lastRun = {run.isoformat()}Z")

    base_out = Path(args.output)

    info = DOMAINS[args.domain]

    # Paket listesi
    if args.packages:
        packages = [p.strip() for p in args.packages.split(",") if p.strip()]
    else:
        packages = info["packages_surface"] + info["packages_pressure"]

    package_times = info["package_times"]

    print(f"[INFO] Domain      : {args.domain}")
    print(f"[INFO] Run (UTC)   : {run.isoformat()}Z")
    print(f"[INFO] Packages    : {packages}")
    print(f"[INFO] Time groups : {package_times}")
    if args.max_forecast_hour is not None:
        print(f"[INFO] Max forecast hour: {args.max_forecast_hour}")

    for package_time in package_times:
        # Örn. "000H012H" -> start=0, end=12
        try:
            start_str = package_time.split("H")[0]
            start_hour = int(start_str)
        except Exception:
            start_hour = None

        if args.max_forecast_hour is not None and start_hour is not None:
            if start_hour > args.max_forecast_hour:
                print(f"[INFO] Skipping {package_time} (start={start_hour}h > {args.max_forecast_hour}h)")
                continue

        for package in packages:
            url = build_gov_url(args.domain, run, package, package_time)
            out_name = f"{args.domain}_{run.strftime('%Y%m%d%H')}_{package}_{package_time}.grib2"
            out_path = base_out / out_name

            # Eğer dosya zaten varsa, tekrar indirme
            if out_path.exists():
                print(f"[SKIP] {out_path} zaten var, atlanıyor.")
                continue

            ok = download_file(url, out_path)
            if not ok:
                # Devam ediyoruz; bazı paketler/koşumlar henüz hazır olmayabilir
                print(f"[WARN] Download başarısız: {url}")


if __name__ == "__main__":
    main()
