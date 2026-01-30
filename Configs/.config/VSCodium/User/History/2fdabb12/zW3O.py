# -*- coding: utf-8 -*-
import os
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, Any, Union

load_dotenv()

class EpiasTransparencyerServices:
    def __init__(self):
        self.main_url = "https://seffaflik.epias.com.tr/electricity-service"
        # Using a session for connection pooling (better performance)
        self.session = requests.Session()
        self.session.headers.update({
            "Accept-Language": "en",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    @staticmethod
    def tgt() -> requests.Response:
        """
        EPIAS Seffaflik Ticket Granting Ticket (TGT) Servisi
        Note: This is static as it doesn't require main_url
        """
        url = "https://giris.epias.com.tr/cas/v1/tickets"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {
            "username": os.getenv("EPIAS_TRANSPARENCY_USERNAME"),
            "password": os.getenv("EPIAS_TRANSPARENCY_PASSWORD"),
        }
        return requests.post(url, headers=headers, data=data)

    def _post(self, endpoint: str, tgt: str, payload: Dict[str, Any]) -> requests.Response:
        """Internal helper to minimize code duplication."""
        url = f"{self.main_url}/{endpoint}"
        headers = {"TGT": tgt}
        return self.session.post(url, headers=headers, json=payload)

    def _format_dates(self, start: str, end: str) -> Dict[str, str]:
        """Helper to format dates for EPIAS API."""
        return {
            "startDate": f"{start}T00:00:00+03:00",
            "endDate": f"{end}T23:00:00+03:00"
        }

    def mcp(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """Piyasa Takas Fiyati (PTF) Servisi"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/dam/data/mcp", tgt, payload)

    def smp(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """Sistem Marjinal Fiyati (SMF) Servisi"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/bpm/data/smp", tgt, payload)

    def real_time_generation(self, tgt: str, start_date: str, end_date: str, powerplant_id:Union[int,None]=None) -> requests.Response:
        """Gercek Zamanli Uretim (GZUP) Servisi"""
        payload = self._format_dates(start_date, end_date)
        payload["powerPlantId"] = powerplant_id
        return self._post("v1/production/data/real-time-generation", tgt, payload)

    def real_time_consumption(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """Gercek Zamanli Uretim (GZUP) Servisi"""
        payload = self._format_dates(start_date, end_date)
        return self._post("/v1/consumption/data/realtime-consumption", tgt, payload)

    def info_powerplant_list(self, tgt: str) -> requests.Response:
        """Santral Listeleme Servisi"""
        return self._post("v1/production/data/powerplant-list", tgt, {})

    def idm_matching_quantity(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """GIP Eslesme Miktari Listeleme Servisi"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/idm/data/matching-quantity", tgt, payload)

    def idm_min_max_bid_price(self, tgt: str, start_date: str, end_date: str) -> requests.Response:
        """GIP Min - Maks Alis Teklif Fiyati Listeleme Servisi"""
        payload = self._format_dates(start_date, end_date)
        return self._post("v1/markets/idm/data/min-max-bid-price", tgt, payload)