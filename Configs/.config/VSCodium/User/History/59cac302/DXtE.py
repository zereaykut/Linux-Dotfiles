from src.utils import EpysClient
from datetime import date, timedelta
import pandas as pd

def main():
    client = EpysClient()
    today = date.today()
    yesterday = today - timedelta(days=1)

    # 1. KUPST (Settlement Based Final Generation Plan)
    client.fetch_and_save(
        url="https://epys.epias.com.tr/reconciliation-bpm/v1/reconciliation/sbfgp",
        payload={
            "effectiveDateStart": f"{yesterday}T00:00:00+03:00",
            "effectiveDateEnd": f"{today}T00:00:00+03:00",
            "page": {"number": 1, "size": 100}
        },
        filename="kupst_data"
    )

    # 2. GOP / GIP (Market Matching Results)
    client.fetch_and_save(
        url="https://epys.epias.com.tr/reconciliation-market/v1/matching-result/list",
        payload={
            "deliveryDayStart": f"{yesterday}T00:00:00+03:00",
            "deliveryDayEnd": f"{today}T23:00:00+03:00",
            "page": {"number": 1, "size": 100}
        },
        filename="gop_gip_results"
    )

    # 3. OSOS (Automatic Meter Reading)
    client.fetch_and_save(
        url="https://epys.epias.com.tr/reconciliation-market/v1/osos-data/list", # Example endpoint
        payload={
            "startDate": f"{yesterday}T00:00:00+03:00",
            "endDate": f"{today}T23:00:00+03:00",
            "page": {"number": 1, "size": 100}
        },
        filename="osos_data"
    )

if __name__ == "__main__":
    main()