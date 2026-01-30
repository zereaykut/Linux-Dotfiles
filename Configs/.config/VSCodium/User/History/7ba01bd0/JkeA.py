import pandas as pd
import numpy as np
from typing import Literal, Dict

class EnergyImbalanceEngine:
    """
    Unified engine for Turkish Electricity Market imbalance and KUPST calculations.
    """

    @staticmethod
    def get_regulation_period(date: pd.Timestamp) -> str:
        """Determines if the date falls under the 2026 regulation."""
        return "26_01" if date >= pd.Timestamp("2026-01-01") else "pre_2026"

    @staticmethod
    def calculate_prices_pre_2026(mcp: float, smp: float, k: float = 0.03) -> Dict[str, float]:
        """Classic margin-based pricing (pre-2026)."""
        return {
            "pos_price": min(mcp, smp) * (1 - k),
            "neg_price": max(mcp, smp) * (1 + k)
        }

    @staticmethod
    def calculate_prices_2026(
        mcp: float, 
        smp: float, 
        v_threshold: float = 750.0, 
        b_penalty: float = 100.0,
        low_m: float = 0.03, 
        high_m: float = 0.06
    ) -> Dict[str, float]:
        """2026+ pricing logic with dynamic margins and floor/ceiling handling."""
        # System direction logic
        neg_m, pos_m = (low_m, high_m) if mcp > smp else (high_m, low_m) if mcp < smp else (low_m, low_m)
        
        # Negative Imbalance Price (Deficit)
        neg_price = max(mcp, smp, v_threshold) * (1 + neg_m)
        
        # Positive Imbalance Price (Surplus)
        pos_raw = min(mcp, smp)
        pos_price = -b_penalty * (1 + pos_m) if pos_raw < v_threshold else pos_raw * (1 - pos_m)
        
        return {"pos_price": pos_price, "neg_price": neg_price}

def calculate_imbalance_cost(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main pipeline to process a dataset and calculate costs based on the date.
    """
    engine = EnergyImbalanceEngine()
    res = df.copy()
    
    def process_row(row):
        period = engine.get_regulation_period(row['Date'])
        if period == "26_01":
            prices = engine.calculate_prices_2026(row['PTF'], row['SMF'])
        else:
            prices = engine.calculate_prices_pre_2026(row['PTF'], row['SMF'])
            
        qty = row['Generation_Real'] - row['Generation_Plan']
        price = prices['pos_price'] if qty >= 0 else prices['neg_price']
        
        return pd.Series({
            "Imbalance_Qty": qty,
            "Unit_Price": price,
            "Total_Cost": qty * price
        })

    results = res.apply(process_row, axis=1)
    return pd.concat([res, results], axis=1)