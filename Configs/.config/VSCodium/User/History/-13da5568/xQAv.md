# EPIAS Energy Imbalance Cost Calculator

A robust Python engine for calculating **Energy Imbalance Costs** in the Turkish Electricity Market (EPIAS). This project is specifically designed to handle the regulatory transition effective **January 1, 2026**, switching automatically between legacy static margins and the new dynamic margin/penalty mechanisms.

## 📋 Features

* **Dual-Regulation Logic:** Automatically detects the date and applies the correct regulation:
    * **Pre-2026:** Classic static margin pricing ($k=0.03$).
    * **Post-2026:** Complex dynamic margins ($0.03$ / $0.06$) with price floors and penalty mechanisms.
* **Threshold Handling:** Implements the new 2026 "V-Threshold" and "B-Penalty" logic for surplus energy when market prices are low.
* **Pandas Native:** Optimized pipeline (`calculate_imbalance_cost`) for processing large time-series datasets efficiently.
* **Unit Tested:** Comprehensive test suite validating edge cases around the 2026 New Year boundary.

## 🗂 Project Structure

```text
.
├── README.md           # Project documentation
├── requirements.txt    # Dependencies (pandas, numpy, pytest)
├── src
│   ├── __init__.py
│   └── utils.py        # Core calculation engine & regulation logic
└── test.py             # Unit tests