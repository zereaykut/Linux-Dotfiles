# EPIAS Transparency Platform Data Automation

A robust, modular Python framework designed to automate the retrieval of energy market data from the **EPIAS Transparency Platform (EPİAŞ Şeffaflık Platformu)**. This project handles authentication, session management, and bulk data extraction. For more information there is [API docs](https://seffaflik-prp.epias.com.tr/electricity-service/technical/tr/index.html).

## 📋 Project Overview

This tool allows Data Scientists and Energy Analysts to:
* **Authenticate** securely using the EPIAS CAS (Central Authentication Service).
* **Persist** data in structured JSON formats for downstream modeling or analysis.

## 📂 Project Structure

The project is organized into a modular structure separating configuration, data, and logic:

```text
├── data/
│   ├── powerplants_info.json           # [Output] Complete registry of all power plants
│   ├── selected_powerplants.json       # [Config] User-defined list of plants to scrape
│   ├── tgt.json                        # [Cache] Active Session Token (TGT)
│   └── selected_powerplants_data/      # [Output] Time-series data per plant
│       ├── {name}_{id}.json
│       └── ...
├── scripts/
│   ├── tgt.py                          # Authentication script
│   ├── powerplants_info.py             # Metadata retrieval script
│   └── selected_powerplants_grt.py     # Main data extraction script
├── src/
│   ├── services.py                     # API Wrapper & Session Manager
│   ├── utils.py                        # I/O helpers and configuration loaders
│   └── __init__.py                     # Package initialization & Logging setup
├── .env                                # Secrets (Username/Password)
├── requirements.txt                    # Python dependencies
└── README.md
```

## ⚙️ Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/zereaykut/EPIAS-Transparency.git](https://github.com/zereaykut/EPIAS-Transparency.git)
    cd EVDS
    ```

2.  **Create a Virtual Environment (Optional but Recommended)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## 🔐 Configuration

1.  Create a file named `.env` in the root directory of the project.
2.  Add your EPIAS Tranparency info to the file:

    ```env
    EPIAS_TRANSPARENCY_USERNAME=your_username
    EPIAS_TRANSPARENCY_PASSWORD=your_password
    ```

    > **Note:** Do not share your `.env` file or commit it to version control.
