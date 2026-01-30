# EVDS-API
Codes for data retrieval from EVDS TCBM (Türkiye Cumhuriyet Merkez Bankası) API
For more information: https://evds2.tcmb.gov.tr/help/videos/EVDS_Web_Servis_Kullanim_Kilavuzu.pdf

## How to Use
Clone the repo
```shell
git clone https://github.com/zereaykut/EVDS-API.git
cd EVDS-API
```

Create python environment
```shell
python -m venv venv
```

Activate environment in Mac/Linux 
```shell
source venv/bin/activate
```

Activate environment in Windows 
```shell
.\venv\Scripts\activate
```

Install required packages
```shell
pip install -r requirements.txt
```

Add your EPIAS Tranparency info to a .env file like below
```config
EVDS_API_KEY=your_secret_api_key
```
