import unittest
import datetime as dt
from src.components.gfs import GFSDownloader
from src.components.ecmwf import ECMWFDownloader

class TestMeteorologicalModels(unittest.TestCase):
    def setUp(self):
        self.test_date = dt.datetime(2025, 1, 1, 0)

    def test_gfs_url_format(self):
        dl = GFSDownloader(output_dir="./tmp")
        urls = dl.build_urls("gfs025", self.test_date, 24)
        self.assertTrue("gfs.20250101" in urls[0])
        self.assertTrue("f024" in urls[0])

    def test_ecmwf_steps(self):
        dl = ECMWFDownloader(output_dir="./tmp")
        steps = dl.get_forecast_steps(0, "ifs025")
        self.assertIn(144, steps)
        self.assertGreater(len(steps), 50)

if __name__ == "__main__":
    unittest.main()