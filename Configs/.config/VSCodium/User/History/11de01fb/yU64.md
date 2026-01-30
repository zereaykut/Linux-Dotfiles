# Data Retrieval from EPIAS Transparency API
Sample code to retrieve and save data from EPİAŞ Transparency API of Türkiye Electricity Market, that uses requests library.
For more info there is API documentation in here: https://seffaflik-prp.epias.com.tr/electricity-service/technical/tr/index.html

## How to Use
Clone the repo
```shell
git clone https://github.com/zereaykut/Requests-EPIAS
cd Requests-EPIAS
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
