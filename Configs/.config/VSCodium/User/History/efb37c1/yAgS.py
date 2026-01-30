#!/usr/bin/env python3
"""
ECMWF Open Data downloader (Open-Meteo ECMWF kısmının Python versiyonu)

Swift kaynak:
- DownloadEcmwfCommand.swift
- EcmwfDomain.getDownloadForecastSteps(run:)
- EcmwfDomain.getUrl(base:run:hour:)
"""

import argparse
import datetime as dt
import os
from pathlib import Path

import requests


# ---------------------------
# Kullanım
# ---------------------------

# Örneğin 2025-03-01 00Z IFS 0.25° deterministik koşusu için:
# python ecmwf.py \
#     --date 20250301 \
#     --run 0 \
#     --domain ifs025 \
#     --max-forecast-hour 240 \
#     --outdir ecmwf_ifs025_data

# Örnek AIFS single için:
# python ecmwf.py --date 20250220 --run 0 --domain aifs025_single --max-forecast-hour 360



# ---------------------------
# Domain tanımı ve saat adımları
# ---------------------------

class EcmwfDomain:
    """
    Swift EcmwfDomain enum'unun sade Python karşılığı.
    """
    VALID = {
        "ifs04",
        "ifs04_ensemble",
        "ifs025",
        "ifs025_ensemble",
        "wam025",
        "wam025_ensemble",
        "aifs025",
        "aifs025_single",
        "aifs025_ensemble",
    }

    def __init__(self, name: str):
        if name not in self.VALID:
            raise ValueError(f"Unknown ECMWF domain: {name}")
        self.name = name

    @property
    def is_ensemble(self) -> bool:
        # Swift: countEnsembleMember > 1 :contentReference[oaicite:1]{index=1}
        return self.name in {
            "ifs04_ensemble",
            "ifs025_ensemble",
            "wam025_ensemble",
            "aifs025_ensemble",
        }

    @property
    def dt_seconds(self) -> int:
        # Swift: aifs025* -> 6 saat, diğerleri 3 saat :contentReference[oaicite:2]{index=2}
        if self.name in {"aifs025", "aifs025_single", "aifs025_ensemble"}:
            return 6 * 3600
        return 3 * 3600

    @property
    def dt_hours(self) -> int:
        return self.dt_seconds // 3600

    def get_download_forecast_steps(self, run_hour: int):
        """
        Swift: getDownloadForecastSteps(run:) fonksiyonunun bire bir portu. :contentReference[oaicite:3]{index=3}
        """
        if self.name in {"aifs025", "aifs025_single", "aifs025_ensemble"}:
            # 0..360 her dt_hours adımında
            return list(range(0, 360 + self.dt_hours, self.dt_hours))

        full_length = (
            self.is_ensemble or
            self.name == "ifs025" or
            self.name == "wam025"
        )

        if run_hour in (0, 12):
            # 0..144 dt_hours, 150..(360 veya 240) 6-saatlik adım
            first = list(range(0, 144 + self.dt_hours, self.dt_hours))
            last_max = 360 if full_length else 240
            second = list(range(150, last_max + 1, 6))
            return first + second
        elif run_hour in (6, 18):
            # 0..144 veya 0..90 dt_hours
            end = 144 if full_length else 90
            return list(range(0, end + self.dt_hours, self.dt_hours))
        else:
            raise ValueError(f"Invalid run hour: {run_hour}. Must be 0, 6, 12 or 18.")

    def get_urls(self, base: str, run_time: dt.datetime, hour: int):
        """
        Swift: EcmwfDomain.getUrl(base:run:hour:) fonksiyonunun bire bir portu. :contentReference[oaicite:4]{index=4}

        Dönüş:
            Eğer tek dosya ise [url],
            aifs025_ensemble için [control_url, perturbed_url].
        """
        run_str = f"{run_time.hour:02d}"
        date_str = run_time.strftime("%Y%m%d")

        if self.name == "ifs04":
            product = "oper" if run_time.hour in (0, 12) else "scda"
            return [
                f"{base}{date_str}/{run_str}z/ifs/0p4-beta/{product}/"
                f"{date_str}{run_str}0000-{hour}h-{product}-fc.grib2"
            ]

        if self.name == "wam025":
            product = "wave" if run_time.hour in (0, 12) else "scwv"
            return [
                f"{base}{date_str}/{run_str}z/ifs/0p25/{product}/"
                f"{date_str}{run_str}0000-{hour}h-{product}-fc.grib2"
            ]

        if self.name == "wam025_ensemble":
            product = "waef" if run_time.hour in (0, 12) else "scda"
            return [
                f"{base}{date_str}/{run_str}z/ifs/0p25/{product}/"
                f"{date_str}{run_str}0000-{hour}h-{product}-ef.grib2"
            ]

        if self.name == "ifs04_ensemble":
            return [
                f"{base}{date_str}/{run_str}z/ifs/0p4-beta/enfo/"
                f"{date_str}{run_str}0000-{hour}h-enfo-ef.grib2"
            ]

        if self.name == "ifs025":
            product = "oper" if run_time.hour in (0, 12) else "scda"
            return [
                f"{base}{date_str}/{run_str}z/ifs/0p25/{product}/"
                f"{date_str}{run_str}0000-{hour}h-{product}-fc.grib2"
            ]

        if self.name == "ifs025_ensemble":
            return [
                f"{base}{date_str}/{run_str}z/ifs/0p25/enfo/"
                f"{date_str}{run_str}0000-{hour}h-enfo-ef.grib2"
            ]

        if self.name == "aifs025":
            return [
                f"{base}{date_str}/{run_str}z/aifs/0p25/oper/"
                f"{date_str}{run_str}0000-{hour}h-oper-fc.grib2"
            ]

        if self.name == "aifs025_single":
            # Swift’teki yorum:
            # https://data.ecmwf.int/forecasts/20250220/00z/aifs-single/0p25/experimental/oper/
            return [
                f"{base}{date_str}/{run_str}z/aifs-single/0p25/oper/"
                f"{date_str}{run_str}0000-{hour}h-oper-fc.grib2"
            ]

        if self.name == "aifs025_ensemble":
            # control + perturbed için iki dosya
            return [
                f"{base}{date_str}/{run_str}z/aifs-ens/0p25/enfo/"
                f"{date_str}{run_str}0000-{hour}h-enfo-cf.grib2",
                f"{base}{date_str}/{run_str}z/aifs-ens/0p25/enfo/"
                f"{date_str}{run_str}0000-{hour}h-enfo-pf.grib2",
            ]

        raise ValueError(f"Unknown domain for URL mapping: {self.name}")


# ---------------------------
# İndirme fonksiyonu
# ---------------------------

def download_file(url: str, out_path: Path, timeout: int = 60):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  -> {url}")
    resp = requests.get(url, stream=True, timeout=timeout)
    if resp.status_code != 200:
        print(f"     !!! HTTP {resp.status_code} – skipping")
        return False

    tmp_path = out_path.with_suffix(out_path.suffix + ".part")

    with tmp_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=1_048_576):
            if chunk:
                f.write(chunk)

    tmp_path.rename(out_path)
    print(f"     saved to {out_path}")
    return True


# ---------------------------
# CLI
# ---------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Download ECMWF Open Data (Open-Meteo ECMWF downloader, Python version)."
    )
    p.add_argument(
        "--date",
        required=True,
        help="Run date in YYYYMMDD format (ör: 20250301)",
    )
    p.add_argument(
        "--run",
        type=int,
        choices=[0, 6, 12, 18],
        required=True,
        help="Run hour (0, 6, 12, 18)",
    )
    p.add_argument(
        "--domain",
        default="ifs04",
        choices=sorted(EcmwfDomain.VALID),
        help="ECMWF domain (default: ifs04)",
    )
    p.add_argument(
        "--max-forecast-hour",
        type=int,
        default=None,
        help="Opsiyonel: sadece bu saate kadar forecast indir (örn. 72).",
    )
    p.add_argument(
        "--outdir",
        default="ecmwf_data",
        help="Çıktı klasörü (GRIB dosyaları buraya yazılır).",
    )
    p.add_argument(
        "--base-url",
        default="https://data.ecmwf.int/forecasts/",
        help="Root server URL (Swift kodundaki server parametresi ile aynı).",
    )
    return p.parse_args()


def main():
    args = parse_args()

    domain = EcmwfDomain(args.domain)

    # Run zamanı
    run_date = dt.datetime.strptime(args.date, "%Y%m%d").date()
    run_time = dt.datetime(run_date.year, run_date.month, run_date.day, args.run)

    # Saat adımları
    forecast_hours = domain.get_download_forecast_steps(args.run)
    if args.max_forecast_hour is not None:
        forecast_hours = [h for h in forecast_hours if h <= args.max_forecast_hour]

    print(f"ECMWF Open Data download")
    print(f"  domain       : {domain.name}")
    print(f"  date         : {run_date}")
    print(f"  run          : {args.run:02d} UTC")
    print(f"  dt_hours     : {domain.dt_hours}")
    print(f"  max hour     : {max(forecast_hours) if forecast_hours else 'N/A'}")
    print(f"  n steps      : {len(forecast_hours)}")
    print(f"  base url     : {args.base_url}")
    print(f"  outdir       : {args.outdir}")
    print("")

    outdir = Path(args.outdir)

    for hour in forecast_hours:
        urls = domain.get_urls(args.base_url, run_time, hour)
        for idx, url in enumerate(urls):
            # Dosya ismi: ecmwf_<domain>_YYYYMMDD_HH_<forecastHour>h[_cf/pf].grib2
            suffix = ""
            if domain.name == "aifs025_ensemble":
                suffix = "_cf" if idx == 0 else "_pf"

            filename = f"ecmwf_{domain.name}_{args.date}_{args.run:02d}_{hour:03d}h{suffix}.grib2"
            out_path = outdir / args.date / f"{args.run:02d}z" / filename

            download_file(url, out_path)


if __name__ == "__main__":
    main()
