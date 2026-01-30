# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
import json
import requests
from typing import Union

load_dotenv()

class EpiasTransparencyerServices:
    def __init__(self):
        self.main_url = "https://seffaflik.epias.com.tr/electricity-service"

    def tgt() -> requests.Response:
        """
        EPIAS Seffaflik Ticket Granting Ticket (TGT) Servisi
        """
        
        response = requests.post(
            # "https://giris-prp.epias.com.tr/cas/v1/tickets", # test environment
            "https://giris.epias.com.tr/cas/v1/tickets",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
                },
            data={
                "username": os.getenv("USERNAME_"),
                "password": os.getenv("PASSWORD_")
                }
            )
        return response
    
    def grt(self, tgt:str, start_date:str, end_date:str, grt_id:Union[int,None]=None) -> requests.Response:
        """
        Gercek Zamanli Uretim (Real Time Generation) Servisi
        """
        if grt_id is None:
            json_data = {
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00",
                "region": "TR1"
                }    
        else:
            json_data = {
                    "startDate": f"{start_date}T00:00:00+03:00",
                    "endDate": f"{end_date}T23:00:00+03:00",
                    "powerPlantId": grt_id,
                    "region": "TR1"
                    }
        response = requests.post(
            f"{self.main_url}/v1/generation/data/realtime-generation",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json=json_data        
            )
        return response
    
    def info_powerplant_list(self, tgt:str) -> requests.Response:
        """
        Santral Listeleme Servisi
        """
        response = requests.get(
            f"{self.main_url}/v1/generation/data/powerplant-list",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            )
        return response
    