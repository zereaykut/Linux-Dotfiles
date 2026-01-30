# EPYS-API
Codes for data retrieval from EPYS

For more info there is API documentation in here: https://seffaflik-prp.epias.com.tr/electricity-service/technical/tr/index.html

## How to Use
Clone the repo
```shell
git clone https://github.com/zereaykut/EPYS-API.git
cd EPIAS-Transparency-API
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
EPIAS_TRANSPARENCY_USERNAME=your_username
EPIAS_TRANSPARENCY_PASSWORD=your_password
```