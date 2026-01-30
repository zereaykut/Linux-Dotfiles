# EPYS-API
Codes for data retrieval from EPYS

For more info there are API documentations in here: 
- https://epys.epias.com.tr/pre-reconciliation/technical/tr/index.html
- https://epys.epias.com.tr/reconciliation-bpm/technical/tr/index.html
- https://epys.epias.com.tr/reconciliation-market/technical/tr/index.html
- https://epys.epias.com.tr/reconciliation-imbalance/technical/tr/index.html
- https://epys.epias.com.tr/reconciliation-rbs/technical/tr/index.html
- https://epys.epias.com.tr/reconciliation-mof/technical/tr/index.html
- https://epys.epias.com.tr/reconciliation-res/technical/tr/index.html


## How to Use
Clone the repo
```shell
git clone https://github.com/zereaykut/EPYS-API.git
cd EPYS-API
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
EPYS_USERNAME=your_username
EPYS_PASSWORD=your_password
EPYS_ORG_NAME=your_organisation_name
```