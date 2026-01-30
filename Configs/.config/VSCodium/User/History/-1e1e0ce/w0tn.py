import requests
import logging
from pathlib import Path
from abc import ABC, abstractmethod

class BaseDownloader(ABC):
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    @abstractmethod
    def get_forecast_steps(self, *args, **kwargs):
        pass

    @abstractmethod
    def build_urls(self, *args, **kwargs):
        pass

    def download_file(self, url: str, custom_filename: str = None):
        filename = custom_filename or url.split("/")[-1]
        target_path = self.output_dir / filename
        
        if target_path.exists():
            return str(target_path)

        try:
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            logging.info(f"Downloaded: {filename}")
            return str(target_path)
        except Exception as e:
            logging.error(f"Failed {url}: {e}")
            return None