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
                "username": os.getenv("EPIAS_TRANSPARENCY_USERNAME"),
                "password": os.getenv("EPIAS_TRANSPARENCY_PASSWORD")
                }
            )
        return response
    
    def mcp(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        Piyasa Takas Fiyati (PTF) Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/mcp",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response
    
    def sfc(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        Sekonder Frekans Kontrolu (SFK) Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/ancillary-services/data/secondary-frequency-capacity-price",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def smp(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        Sistem Marjinal Fiyati Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/bpm/data/system-marginal-price",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response
    
    def system_direction(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        Sistem Yonu Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/bpm/data/system-direction",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def consumption(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        Turkiye Gercek Zamanli Tuketim Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/consumption/data/realtime-consumption",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def kgup(self, tgt:str, start_date:str, end_date:str, organization_id:Union[int,None]=None, uevcb_id:Union[int,None]=None) -> requests.Response:
        """
        KGUP Servisi
        """
        if (organization_id is None) | (uevcb_id is None):
            json_data = {
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00",
                "region": "TR1"
                }    
        else:
            json_data = {
                    "startDate": f"{start_date}T00:00:00+03:00",
                    "endDate": f"{end_date}T23:00:00+03:00",
                    "organizationId": organization_id,
                    "uevcbId": uevcb_id,
                    "region": "TR1"
                    }
        response = requests.post(
            f"{self.main_url}/v1/generation/data/dpp",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json=json_data        
            )
        return response
    
    def first_kgup(self, tgt:str, start_date:str, end_date:str, organization_id:Union[int,None]=None, uevcb_id:Union[int,None]=None) -> requests.Response:
        """
        First KGUP Servisi
        """
        if (organization_id is None) | (uevcb_id is None):
            json_data = {
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00",
                "region": "TR1"
                }    
        else:
            json_data = {
                    "startDate": f"{start_date}T00:00:00+03:00",
                    "endDate": f"{end_date}T23:00:00+03:00",
                    "organizationId": organization_id,
                    "uevcbId": uevcb_id,
                    "region": "TR1"
                    }
        response = requests.post(
            f"{self.main_url}/v1/generation/data/dpp-first-version",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json=json_data        
            )
        return response


    def eak(self, tgt:str, start_date:str, end_date:str, organization_id:Union[int,None]=None, uevcb_id:Union[int,None]=None) -> requests.Response:
        """
        EAK Servisi
        """
        if (organization_id is None) | (uevcb_id is None):
            json_data = {
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00",
                "region": "TR1"
                }    
        else:
            json_data = {
                    "startDate": f"{start_date}T00:00:00+03:00",
                    "endDate": f"{end_date}T23:00:00+03:00",
                    "organizationId": organization_id,
                    "uevcbId": uevcb_id,
                    "region": "TR1"
                    }
        response = requests.post(
            f"{self.main_url}/v1/generation/data/aic",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json=json_data        
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
    
    def uevm(self, tgt:str, start_date:str, end_date:str, uevm_id:Union[int,None]=None) -> requests.Response:
        """
        Uzlastirma Esas Veris Miktari Servisi
        """
        if uevm_id is None:
            json_data = {
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00",
                "region": "TR1"
                }    
        else:
            json_data = {
                    "startDate": f"{start_date}T00:00:00+03:00",
                    "endDate": f"{end_date}T23:00:00+03:00",
                    "powerplantId": uevm_id,
                    "region": "TR1"
                    }
        response = requests.post(
            f"{self.main_url}/v1/generation/data/injection-quantity",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json=json_data        
            )
        return response

    def kudup(self, tgt:str, start_date:str, end_date:str, organization_id:Union[int,None]=None, uevcb_id:Union[int,None]=None) -> requests.Response:
        """
        KUDUP Servisi
        """
        if (organization_id is None) | (uevcb_id is None):
            json_data = {
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00",
                "region": "TR1"
                }    
        else:
            json_data = {
                    "startDate": f"{start_date}T00:00:00+03:00",
                    "endDate": f"{end_date}T23:00:00+03:00",
                    "organizationId": organization_id,
                    "uevcbId": uevcb_id,
                    "region": "TR1"
                    }
        response = requests.post(
            f"{self.main_url}/v1/generation/data/sbfgp",
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
    
    def info_yekdem_powerplant_list(self, tgt:str, period:str) -> requests.Response:
        """
        Lisanslı Santral Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/renewables/data/licensed-powerplant-list",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
            "period": f"{period}T00:00:00+03:00"
            }
            )
        return response

    def info_injection_quantity_powerplant_list(self, tgt:str) -> requests.Response:
        """
        Uzlastirma Esas Veris Miktari (UEVM) Santral Listesi Servisi
        """
        response = requests.get(
            f"{self.main_url}/v1/generation/data/injection-quantity-powerplant-list",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            )
        return response
    
    def info_organization_list(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        Organizasyon Listesi Getirme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/generation/data/organization-list",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response
    
    def info_powerplant_list_date_range(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        Organizasyon Listesi Getirme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/generation/data/powerplant-list-for-date-range",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response
    
    def info_uevcb_list(self, tgt:str, start_date:str, organization_id:int) -> requests.Response:
        """
        Uevcb Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/generation/data/uevcb-list",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "organizationId": organization_id
                }        
            )
        return response

    def info_injection_quantity_powerplant_list(self, tgt:str) -> requests.Response:
        """
        Uzlastirma Esas Veris Miktari (UEVM) Santral Listesi Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/generation/data/injection-quantity-powerplant-list",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                }
            )
        return response
    
    def info_uevcb_list_by_power_plant_id(self, tgt:str, start_date:str, powerplant_id:int) -> requests.Response:
        """
        Piyasa Mesaj Sistemi Uevcb Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/data/uevcb-list-by-power-plant-id",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "powerPlantId": powerplant_id,
                }        
            )
        return response

    def dam_block_buy(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Blok Alis Miktari Listeleme Servisi
        Gun Oncesi Piyasasi’nda sunulan en az 4 en fazla 24 saati kapsayan ve eslesen blok alis tekliflerinin toplam miktaridir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/amount-of-block-buying",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response
    
    def dam_block_sell(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Blok Satis Miktari Listeleme Servisi
        Gun Oncesi Piyasasi’nda sunulan en az 4 en fazla 24 saati kapsayan ve eslesen blok satis tekliflerinin toplam miktaridir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/amount-of-block-selling",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response
    
    def dam_match_volume(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Eslesme Miktari Listeleme Servisi
        Gun Oncesi Piyasasi’nda eslesen tekliflerin saatlik toplam miktardir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/clearing-quantity",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def dam_trade_volume(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Islem Hacmi Listeleme Servisi
        Gun Oncesi Piyasasi’nda eslesen alis tekliflerinin saatlik toplam mali degeridir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/day-ahead-market-trade-volume",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def dam_flexible_offer_buying_quantity(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Esnek Alis Teklif Miktari Listeleme Servisi
        Gun Oncesi piyasasina katilan piyasa katilimcisinin, belirli bir teklif zaman araliginda belirtilen teklif suresi icin, lot cinsinden uzlastirma donemi bazli 
        degisebilen alis miktarlarini eslesen ve eslesmeyen teklif kiriliminda icerir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/flexible-offer-buying-quantity",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def dam_flexible_offer_selling_quantity(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Esnek Satis Teklif Miktari Listeleme Servisi
        Gun Oncesi piyasasina katilan piyasa katilimcisinin, belirli bir teklif zaman araliginda belirtilen teklif suresi icin, lot cinsinden uzlastirma dOnemi bazli 
        degisebilen satis miktarlarini eslesen ve eslesmeyen teklif kiriliminda icerir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/flexible-offer-selling-quantity",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def dam_matched_flexible_offer_quantity(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Esnek Teklif Eslesme Miktarlari Listeleme Servisi
        Esnek Teklif Eslesme Miktarlari Belirli bir teklif zaman araligi boyunca belirli bir teklif suresi icin degisebilen miktarlardan ve bu miktarlar icin tek fiyat 
        bilgilerinden olusan esnek tekliflerin alis ve satis yOnlu eslesme miktarlari
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/matched-flexible-offer-quantity",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def dam_price_independent_bid(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Fiyattan Bagimsiz Alis Teklifi Listeleme Servisi
        Gun Oncesi piyasasinda saatlik olarak fiyat kirilimi olusturulmadan sunulan alis tekliflerinin toplamidir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/price-independent-bid",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def dam_price_independent_offer(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Fiyattan Bagimsiz Satis Teklifi Listeleme Servisi
        Gun Oncesi piyasasinda saatlik olarak fiyat kirilimi olusturulmadan sunulan satis tekliflerinin toplamidir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/price-independent-offer",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def dam_side_payments(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Fark Tutari Listeleme Servisi
        Alis tekliflerinden kaynakli fark tutari alis yOnlu blok ve esnek teklif eslesmelerinden, satis tekliflerinden kaynakli fark tutari satis yOnlu blok ve esnek teklif 
        eslesmelerinden kaynaklanmaktadir.Fark tutari hesaplanmasi ve dagitilmasina iliskin detaylar Fark Tutari Proseduru’nde yer almaktadir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/side-payments",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response
    
    def dam_submitted_bid_order_volume(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Teklif Edilen Alis Miktarlari Listeleme Servisi
        Gun Oncesi Piyasasi’nda 0 TL/MWh fiyat seviyesine sunulan saatlik, blok ve esnek alis teklif miktarlarinin toplamidir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/submitted-bid-order-volume",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response

    def dam_submitted_sales_order_volume(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GOP Teklif Edilen Satis Miktarlari Listeleme Servisi
        Gun Oncesi Piyasasi’nda azami uzlastirma fiyat seviyesine sunulan saatlik, blok ve esnek satis teklif miktarlarinin toplamidir.
        Azami Uzlastirma Fiyati 01.10.2023 tarihinden itibaren kaldirilmistir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/submitted-sales-order-volume",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response
    
    def idm_weighted_average_price(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GIP Agirlikli Ortalama Fiyat Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/idm/data/weighted-average-price",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
                }        
            )
        return response
    
    def merit_order(self, tgt:str, date_:str) -> requests.Response:
        """
        Supply Demand Curve, Merit Order
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/dam/data/supply-demand",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "date": date_
                }        
            )
        return response

    def order_summary_down(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        Yuk Atma (YAT) Talimat Miktari Listeleme Servisi
        0, 1, 2 kodlu Alma Talimat Miktari (YAT), sistem yonunde elektrik fazlasi durumlarda sistemi dengelemek icin verilen talimat miktaridir. Veriler 4 saat onceki talimatlari yansitmaktadir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/bpm/data/order-summary-down",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00",
                "region": "TR1"
                }        
            )
        return response
    
    def order_summary_up(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        Yuk Alma (YAL) Talimat Miktarlari Listeleme Servisi
        0, 1, 2 kodlu Alma Talimat Miktari (YAL), sistem yonunde elektrik acigi durumlarda sistemi dengelemek icin verilen talimat miktaridir. Veriler 4 saat onceki talimatlari yansitmaktadir.
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/bpm/data/order-summary-up",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00",
                "region": "TR1"
                }        
            )
        return response

    def dam_active_fullness(self, tgt:str) -> requests.Response:
        """
        Debi ve Kurulu Guc Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/dams/data/active-fullness",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={}
            )
        return response
    
    def dam_flow_rate_and_installed_power(self, tgt:str) -> requests.Response:
        """
        Debi ve Kurulu Guc Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/dams/data/flow-rate-and-installed-power",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={}
            )
        return response
    
    def dam_water_energy_provision(self, tgt:str) -> requests.Response:
        """
        Suyun Enerji Karsiligi Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/dams/data/water-energy-provision",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={}
            )
        return response

    def dam_daily_volume(self, tgt:str) -> requests.Response:
        """
        Gunluk Hacim Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/dams/data/daily-volume",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "region":"TR1"
                }
            )
        return response

    def dam_daily_kot(self, tgt:str) -> requests.Response:
        """
        Gunluk Kot Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/dams/data/daily-kot",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "region":"TR1"
                }
            )
        return response

    def dam_volume(self, tgt:str) -> requests.Response:
        """
        Hacim Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/dams/data/dam-volume",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "region":"TR1"
                }
            )
        return response

    def dam_kot(self, tgt:str) -> requests.Response:
        """
        Suyun Enerji Karsiligi Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/dams/data/dam-kot",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={}
            )
        return response
    
    def idm_trade_hist(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GIP Teklif Edilen Alis Satis Fiyatlari ve Miktarlari Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/idm/data/transaction-history",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
            }
            )
        return response
    
    def idm_trade_vol(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GIP Teklif Edilen Alis Satis Miktarlari Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/idm/data/trade-value",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
            }
            )
        return response
    
    def idm_min_max_sales_offer_price(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GIP Min - Maks Satis Teklif Fiyati Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/idm/data/min-max-sales-offer-price",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
            }
            )
        return response
    
    def idm_min_max_match_price(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GIP Min - Maks Eslesme Fiyat Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/idm/data/min-max-matching-price",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
            }
            )
        return response
    
    def idm_bid_offer_quantity(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GIP Teklif Edilen Alis Satis Miktarlari Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/idm/data/bid-offer-quantities",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
            }
            )
        return response
    
    def idm_matching_quantity(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GIP Eslesme Miktari Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/idm/data/matching-quantity",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
            }
            )
        return response
    
    def idm_min_max_bid_price(self, tgt:str, start_date:str, end_date:str) -> requests.Response:
        """
        GIP Min - Maks Alis Teklif Fiyati Listeleme Servisi
        """
        response = requests.post(
            f"{self.main_url}/v1/markets/idm/data/min-max-bid-price",
            headers={
                "Accept-Language": "en",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "TGT": tgt
                },
            json={
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
            }
            )
        return response