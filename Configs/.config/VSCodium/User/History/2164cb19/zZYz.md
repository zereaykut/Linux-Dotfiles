For more information: https://evds2.tcmb.gov.tr/help/videos/EVDS_Web_Servis_Kullanim_Kilavuzu.pdf

# TCMB EVDS Exchange Rate Fetcher

This project is a robust Python automation tool designed to retrieve historical exchange rate data from the **Central Bank of the Republic of Turkey (TCMB)** using their **EVDS (Electronic Data Delivery System) API**.

It fetches USD and EUR exchange rates (Buying/Selling) for the last 7 days, processes the data, and appends it to a CSV file for archival or analysis purposes.

## 🚀 Features

* **Automated Date Handling:** Automatically calculates the date range for the last week relative to the current execution date.
* **Robust API Requests:** Implements a retry mechanism (exponential backoff) to handle network fluctuations or API rate limits gracefully.
* **Secure Configuration:** Uses environment variables to securely manage the EVDS API Key.
* **Data Persistence:** Appends new data to an existing CSV file (`exchange_rates.csv`), creating the file if it doesn't exist.
* **Error Handling:** Includes a custom exception handler to capture and report detailed error information (file name, line number).
* **Data Cleaning:** Automatically cleans the response by dropping unnecessary columns (like UNIXTIME) and handling missing values using forward fill.

## 📂 Project Structure

├── data/
│   └── processed/
│       └── exchange_rates.csv    # Generated output file
├── src/
│   ├── __init__.py
│   ├── exception.py              # Custom exception handling logic
│   └── utils.py                  # Helper functions (API fetch, CSV save, Env vars)
├── .env                          # Environment variables (not committed to git)
├── .gitignore                    # Git ignore rules
├── app.py                        # Main entry point of the application
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation

## 🛠️ Prerequisites

* Python 3.8 or higher
* An active API Key from [TCMB EVDS](https://evds2.tcmb.gov.tr/index.php?/evds/login) (Sign up is free).

## ⚙️ Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/zereaykut/EVDS.git](https://github.com/zereaykut/EVDS.git)
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
2.  Add your EVDS API key to the file:

    ```env
    EVDS_API_KEY=your_actual_api_key_here
    ```

    > **Note:** Do not share your `.env` file or commit it to version control.

## ▶️ Usage

To run the application, simply execute the `app.py` script:

```bash
python app.py