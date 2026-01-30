import pytest
import pandas as pd
from src.utils import EnergyImbalanceEngine, calculate_imbalance_cost

def test_regulation_logic_switch():
    """Tests if the system correctly identifies the 2026 boundary."""
    data = {
        "Date": pd.to_datetime(["2025-12-31 23:00", "2026-01-01 01:00"]),
        "PTF": [2000, 2000],
        "SMF": [2100, 2100],
        "Generation_Plan": [100, 100],
        "Generation_Real": [90, 90] # 10 MWh Deficit
    }
    df = pd.DataFrame(data)
    result = calculate_imbalance_cost(df)
    
    # 2025: max(2000, 2100) * 1.03 = 2163
    assert result.iloc[0]['Unit_Price'] == 2163.0
    
    # 2026: max(2000, 2100, 750) * (1 + 0.06 [since mcp < smp]) = 2100 * 1.06 = 2226
    assert result.iloc[1]['Unit_Price'] == 2226.0

def test_negative_surplus_price_2026():
    """Tests the 2026 'B penalty' when prices are below threshold V."""
    engine = EnergyImbalanceEngine()
    # MCP/SMP (500) is below V (750)
    prices = engine.calculate_prices_2026(mcp=500, smp=500, v_threshold=750, b_penalty=100)
    
    # Positive imbalance price should be -B * (1 + low_m) = -100 * 1.03 = -103
    assert prices['pos_price'] == -103.0

def test_full_pipeline_output():
    """Tests if columns are correctly added to the dataframe."""
    data = {
        "Date": [pd.Timestamp("2025-01-01")],
        "PTF": [1000.0],
        "SMF": [1000.0],
        "Generation_Plan": [100.0],
        "Generation_Real": [110.0]
    }
    df = pd.DataFrame(data)
    result = calculate_imbalance_cost(df)
    
    assert "Imbalance_Qty" in result.columns
    assert "Total_Cost" in result.columns
    assert result.iloc[0]["Imbalance_Qty"] == 10.0