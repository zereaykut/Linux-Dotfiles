import os
import cdsapi
import zipfile
import pandas as pd


def data_downloader(request: dict):
    os.makedirs("data", exist_ok=True)
    dataset = "sis-energy-derived-projections"
    client = cdsapi.Client()
    client.retrieve(dataset, request).download("data/projection-data.zip")


def extract_data(
    zip_path: str = "data/climate-data.zip",
    extract_to: str = "data/extracted-climate_data",
):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


def data_prep(loc: str, col: str = "TR", index: str = "Date", skiprows: int = None) -> pd.DataFrame:
    df = pd.read_csv(loc, skiprows=skiprows)
    df[index] = pd.to_datetime(df[index])
    df = df.set_index(index)
    return df[[col]]
