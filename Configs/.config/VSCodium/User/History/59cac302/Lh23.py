from src.utils import EpysClient
from datetime import date, timedelta
import os

def main():
    # Initialize client (points to your existing credentials file)
    creds_path = os.path.join("data", "password", "epias_epys_password.json")
    client = EpysClient(creds_path)

    # Common Parameters
    today = date.today()
    d_1 = today - timedelta(days=1)
    
    # Example for KUPST (SBFGP)
    kupst_url = "https://epys.epias.com.tr/reconciliation-bpm/v1/reconciliation/sbfgp"
    
    # Example for GOP/GIP (Matching Results)
    gop_url = "https://epys.epias.com.tr/reconciliation-market/v1/matching-result/list"

    for user_key, info in client.credentials.items():
        headers = client.get_headers(info['username'], info['password'])
        if not headers:
            continue

        # 1. Fetch KUPST
        kupst_payload = {
            "effectiveDateStart": f"{d_1}T00:00:00+03:00",
            "effectiveDateEnd": f"{today}T00:00:00+03:00",
            "page": {"number": 1, "size": 100}
        }
        client.fetch_and_save(kupst_url, kupst_payload, headers, "epias_kupst", info['org_name'])

        # 2. Fetch GOP/GIP
        gop_payload = {
            "deliveryDayStart": f"{d_1}T00:00:00+03:00",
            "deliveryDayEnd": f"{today}T23:00:00+03:00",
            "page": {"number": 1, "size": 100}
        }
        client.fetch_and_save(gop_url, gop_payload, headers, "epias_gop_gip", info['org_name'])

if __name__ == "__main__":
    main()