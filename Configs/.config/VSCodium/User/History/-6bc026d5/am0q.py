#!/usr/bin/env python3
"""
Simple GFS / GEFS / GFS-Wave downloader inspired by Open-Meteo's GfsDownload.swift.

- Supports domains: gfs013, gfs025, gfs025_ens, gfs05_ens,
                    gfswave025, gfswave016, gfswave025_ens,
                    nam_conus, hrrr_conus, hrrr_conus_15min

- Builds URLs following the same patterns as GfsDomain.getGribUrl in Open-Meteo.
- Forecast hour lists mirror GfsDomain.forecastHours.
"""

import argparse
import datetime as dt
import os
from typing import List
import requests

# Kullanım
# # Son koşuyu tahmin et, gfs 0.25° deterministik indir
# python gfs.py gfs025 --output-dir ./gfs_data

# # Belirli bir koşu (2024-06-19 00 UTC), ilk 120 saati indir
# python gfs.py gfs025 --run 2024061900 --max-forecast-hour 120

# # GEFS 0.5° ensemble, ikinci flush (390–840 saat) ve sadece AWS arşivinden
# python gfs.py gfs05_ens --second-flush --use-aws

# # Wave çıktıları (gfswave 0.25°)
# python gfs.py gfswave025 --output-dir ./gfs_wave

DOMAINS = [
    "gfs013",
    "gfs025",
    "gfs025_ens",
    "gfs05_ens",
    "gfswave025",
    "gfswave016",
    "gfswave025_ens",
    "nam_conus",
    "hrrr_conus",
    "hrrr_conus_15min",
]

# How many ensemble members
ENSEMBLE_MEMBER_COUNT = {
    "gfs05_ens": 31,        # 30 + control
    "gfs025_ens": 31,
    "gfswave025_ens": 31,
}


def floor_to_6h(dt_utc: dt.datetime) -> dt.datetime:
    """Floor datetime to previous 6-hour cycle (00,06,12,18)."""
    hour = (dt_utc.hour // 6) * 6
    return dt_utc.replace(hour=hour, minute=0, second=0, microsecond=0)


def last_run(domain: str, now: dt.datetime | None = None) -> dt.datetime:
    """
    Approximate last run logic similar to GfsDomain.lastRun in Swift.

    - gfs*/gefs/wave: subtract 3 hours, floor to 6h
    - nam_conus:     subtract 1 hour, floor to 6h
    - hrrr_conus*:   use current hour (no 6h floor)
    """
    if now is None:
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)

    if domain in ("gfs05_ens", "gfs025_ens", "gfswave025_ens",
                  "gfs013", "gfs025", "gfswave025", "gfswave016"):
        t = now - dt.timedelta(hours=3)
        return floor_to_6h(t)
    elif domain == "nam_conus":
        t = now - dt.timedelta(hours=1)
        return floor_to_6h(t)
    elif domain in ("hrrr_conus", "hrrr_conus_15min"):
        # Just use latest whole hour
        return now.replace(minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Unknown domain for last_run: {domain}")


def forecast_hours(domain: str, run_hour: int, second_flush: bool) -> List[int]:
    """
    Port of GfsDomain.forecastHours(run:secondFlush:) from Swift.

    - Hours are in forecast hour units.
    """
    if domain == "gfs05_ens":
        if second_flush:
            # 390...840 step 6
            return list(range(390, 841, 6))
        # 0..239 step 3, then 240..384 step 6
        return list(range(0, 240, 3)) + list(range(240, 385, 6))

    if domain in ("gfs025_ens", "gfswave025_ens"):
        # 0..240 step 3
        return list(range(0, 241, 3))

    if domain in ("gfs013", "gfs025", "gfswave025", "gfswave016"):
        # 0..119 hourly, then 120..384 3-hourly
        return list(range(0, 120, 1)) + list(range(120, 385, 3))

    if domain == "nam_conus":
        # 0..60 hourly
        return list(range(0, 61))

    if domain == "hrrr_conus":
        # If run hour multiple of 6 -> 0..48, else 0..18
        if run_hour % 6 == 0:
            return list(range(0, 49))
        else:
            return list(range(0, 19))

    if domain == "hrrr_conus_15min":
        # 0..(18*4) hours (HRRR 15-min logic; GRIB files are hourly buckets)
        return list(range(0, 18 * 4 + 1))

    raise ValueError(f"Unknown domain for forecast_hours: {domain}")


def build_gfs_urls(domain: str,
                   run_dt: dt.datetime,
                   forecast_hour: int,
                   member: int,
                   use_aws: bool) -> List[str]:
    """
    Build GRIB URLs exactly as in GfsDomain.getGribUrl Swift implementation
    (simplified to the parts we need).
    """
    # All times in UTC
    yyyymmdd = run_dt.strftime("%Y%m%d")
    hh = run_dt.strftime("%H")
    fHH = f"{forecast_hour:02d}"
    fHHH = f"{forecast_hour:03d}"

    # Base URLs
    gfsAws = "https://noaa-gfs-bdp-pds.s3.amazonaws.com/"
    gfsNomads = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
    gefsAws = "https://noaa-gefs-pds.s3.amazonaws.com/"
    gefsNomads = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gens/prod/"
    hrrrNomads = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/"
    hrrrAws = "https://noaa-hrrr-bdp-pds.s3.amazonaws.com/"

    # Swift’te: useArchive = useAws || (now - run) > 36h
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    age_sec = (now - run_dt).total_seconds()
    use_archive = use_aws or (age_sec > 36 * 3600)

    gfs_server = gfsAws if use_archive else gfsNomads
    gefs_server = gefsAws if use_archive else gefsNomads
    hrrr_server = hrrrAws if use_archive else hrrrNomads

    if domain == "gfs05_ens":
        # gefs.\(yyyymmdd)/\(hh)/atmos/pgrb2ap5/...
        member_string = "gec00" if member == 0 else f"gep{member:02d}"
        base_a = f"{gefs_server}gefs.{yyyymmdd}/{hh}/atmos/pgrb2ap5"
        base_b = f"{gefs_server}gefs.{yyyymmdd}/{hh}/atmos/pgrb2bp5"
        url_a = f"{base_a}/{member_string}.t{hh}z.pgrb2a.0p50.f{fHHH}"
        url_b = f"{base_b}/{member_string}.t{hh}z.pgrb2b.0p50.f{fHHH}"
        return [url_a, url_b]

    if domain == "gfs025_ens":
        # gefs.\(yyyymmdd)/\(hh)/atmos/pgrb2sp25/...
        member_string = "gec00" if member == 0 else f"gep{member:02d}"
        base = f"{gefs_server}gefs.{yyyymmdd}/{hh}/atmos/pgrb2sp25"
        url = f"{base}/{member_string}.t{hh}z.pgrb2s.0p25.f{fHHH}"
        return [url]

    if domain == "gfs013":
        # gfs.t\(hh)z.sfluxgrbf\(fHHH).grib2
        base = f"{gfs_server}gfs.{yyyymmdd}/{hh}/atmos"
        url = f"{base}/gfs.t{hh}z.sfluxgrbf{fHHH}.grib2"
        return [url]

    if domain == "gfs025":
        # pgrb2 + pgrb2b 0p25°
        base = f"{gfs_server}gfs.{yyyymmdd}/{hh}/atmos"
        url1 = f"{base}/gfs.t{hh}z.pgrb2.0p25.f{fHHH}"
        url2 = f"{base}/gfs.t{hh}z.pgrb2b.0p25.f{fHHH}"
        return [url1, url2]

    if domain == "gfswave025":
        # gfswave.t\(hh)z.global.0p25.f\(fHHH).grib2
        base = f"{gfs_server}gfs.{yyyymmdd}/{hh}/wave/gridded"
        url = f"{base}/gfswave.t{hh}z.global.0p25.f{fHHH}.grib2"
        return [url]

    if domain == "gfswave016":
        base = f"{gfs_server}gfs.{yyyymmdd}/{hh}/wave/gridded"
        url = f"{base}/gfswave.t{hh}z.global.0p16.f{fHHH}.grib2"
        return [url]

    if domain == "gfswave025_ens":
        # gefs.wave.t\(hh)z.c00.global.0p25.f\(fHHH).grib2
        member_string = "c00" if member == 0 else f"p{member:02d}"
        base = f"{gefs_server}gefs.{yyyymmdd}/{hh}/wave/gridded"
        url = f"{base}/gefs.wave.t{hh}z.{member_string}.global.0p25.f{fHHH}.grib2"
        return [url]

    if domain == "nam_conus":
        # nam.\(run.format_YYYYMMdd)/nam.t\(run.hh)z.conusnest.hiresf\(fHH).tm00.grib2
        url = (
            f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/nam/prod/"
            f"nam.{yyyymmdd}/nam.t{hh}z.conusnest.hiresf{fHH}.tm00.grib2"
        )
        return [url]

    if domain == "hrrr_conus":
        url = (
            f"{hrrr_server}hrrr.{yyyymmdd}/conus/"
            f"hrrr.t{hh}z.wrfprsf{fHH}.grib2"
        )
        return [url]

    if domain == "hrrr_conus_15min":
        url = (
            f"{hrrr_server}hrrr.{yyyymmdd}/conus/"
            f"hrrr.t{hh}z.wrfsubhf{fHH}.grib2"
        )
        return [url]

    raise ValueError(f"URL pattern not implemented for domain: {domain}")


def download_file(url: str, out_path: str, timeout: int = 60) -> None:
    """Download a single file with streaming, skip if already exists."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if os.path.exists(out_path):
        print(f"[SKIP] {out_path} (already exists)")
        return

    print(f"[GET ] {url}")
    resp = requests.get(url, stream=True, timeout=timeout)
    if resp.status_code != 200:
        print(f"[WARN] HTTP {resp.status_code} for {url}")
        return

    tmp_path = out_path + ".part"
    with open(tmp_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
    os.rename(tmp_path, out_path)
    print(f"[OK  ] {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download GFS/GEFS/GFS-Wave GRIB files (Open-Meteo style)."
    )
    parser.add_argument(
        "domain",
        choices=DOMAINS,
        help="Model domain (e.g. gfs025, gfs013, gfs025_ens, gfswave025, ...)",
    )
    parser.add_argument(
        "--run",
        help="Run time in YYYYMMDDHH (UTC). If omitted, last available run is estimated.",
    )
    parser.add_argument(
        "--second-flush",
        action="store_true",
        help="For gfs05_ens second flush (390–840h).",
    )
    parser.add_argument(
        "--max-forecast-hour",
        type=int,
        help="If set, only download forecast hours <= this value.",
    )
    parser.add_argument(
        "--output-dir",
        default="./gfs_data",
        help="Base directory to store downloaded GRIB files.",
    )
    parser.add_argument(
        "--use-aws",
        action="store_true",
        help="Prefer AWS archive URLs (useArchive in Swift).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds (per request).",
    )
    parser.add_argument(
        "--max-members",
        type=int,
        default=None,
        help="For ensemble domains: limit number of members (default: all). "
             "Member indices start at 0 (control).",
    )

    args = parser.parse_args()

    domain = args.domain

    # Determine run datetime
    if args.run:
        if len(args.run) != 10:
            raise SystemExit("run must be in YYYYMMDDHH format (10 digits).")
        run_dt = dt.datetime.strptime(args.run, "%Y%m%d%H").replace(
            tzinfo=dt.timezone.utc
        )
    else:
        run_dt = last_run(domain)
    yyyymmddhh = run_dt.strftime("%Y%m%d%H")

    # Forecast hours
    fhours = forecast_hours(domain, run_dt.hour, args.second_flush)
    if args.max_forecast_hour is not None:
        fhours = [h for h in fhours if h <= args.max_forecast_hour]

    # Determine members for ensembles
    if domain in ENSEMBLE_MEMBER_COUNT:
        n_members = ENSEMBLE_MEMBER_COUNT[domain]
        if args.max_members is not None:
            n_members = min(n_members, args.max_members)
        members = list(range(n_members))
    else:
        members = [0]  # deterministic / single-member view

    print(
        f"Domain={domain}, run={yyyymmddhh}Z, "
        f"members={len(members)}, fhours={len(fhours)}"
    )

    session = requests.Session()

    for member in members:
        for fhour in fhours:
            urls = build_gfs_urls(
                domain=domain,
                run_dt=run_dt,
                forecast_hour=fhour,
                member=member,
                use_aws=args.use_aws,
            )
            for url in urls:
                filename = os.path.basename(url)
                out_dir = os.path.join(args.output_dir, domain, yyyymmddhh, f"m{member:02d}")
                out_path = os.path.join(out_dir, filename)
                download_file(url, out_path, timeout=args.timeout)

    session.close()


if __name__ == "__main__":
    main()
