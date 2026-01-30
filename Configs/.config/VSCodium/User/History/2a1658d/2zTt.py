from typing import List
import json

def save_json(data: dict, loc: str) -> None:
    with open(loc, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_selected_powerplants():
    with open("data/selected_powerplants.json", "r", encoding="utf8") as f:
        return json.load(f).get("powerplants_info")

def get_tgt() -> Optional[str]:
    try:
        with open("data/tgt.json", "r", encoding="utf8") as f:
            data = json.load(f)
            return data.get("tgt")
    except FileNotFoundError:
        logging.warning("tgt.json not found. Please run fetch_tgt.py first.")
        return None
    except json.JSONDecodeError:
        logging.error("tgt.json is corrupted.")
        return None
