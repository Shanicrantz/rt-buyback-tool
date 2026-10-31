import unittest
from _research_nonphone_prices import identity_problem

class Identity(unittest.TestCase):
 def row(self,name,category,ram=None,storage=None):return dict(display_name=name,category=category,ram=ram,storage=storage)
 def test_nearby_models_and_accessories_rejected(self):
  cases=[
   (self.row('Samsung Galaxy Watch Ultra 47mm LTE','watch'),'Samsung Galaxy Watch Ultra 2 Smartwatch (47mm LTE, Titanium Silver)'),
   (self.row('Redmi Pad Pro 8/128GB','tablet',8,128),'Redmi Pad 2 Pro 12.1 inch Wi-Fi Tablet 8 GB RAM 128 GB'),
   (self.row('Redmi Pad 4/128GB','tablet',4,128),'Redmi Pad SE 4 GB RAM 128 GB ROM 11 inch Wi-Fi Tablet'),
   (self.row('OnePlus Buds Pro 3','audio'),'EAGLESQUAD OnePlus Buds Pro 3 Bluetooth'),
   (self.row('Nothing Ear (2024)','audio'),'Nothing Ear (a) 2024 ChatGPT Compatible'),
   (self.row('Redmi Watch 5','watch'),'Redmi Watch 5 Active Smartwatch'),
   (self.row('Redmi Pad SE 4/128GB','tablet',4,128),'Redmi Pad SE 4G 4 GB RAM 128 GB ROM'),
   (self.row('Apple Watch Series 10 42mm GPS','watch'),'Apple Watch Series 10 42mm GPS + Cellular'),
   (self.row('Apple AirPods 4','audio'),'Apple AirPods 4 Active Noise Cancellation'),
  ]
  for row,title in cases:
   with self.subTest(title=title):self.assertIsNotNone(identity_problem(row,title))
 def test_exact_products_and_sizes_accepted(self):
  cases=[
   (self.row('Apple AirPods 4 (ANC)','audio'),'Apple AirPods 4 Wireless Earbuds with Active Noise Cancellation'),
   (self.row('Apple Watch Series 10 42mm GPS','watch'),'Apple Watch Series 10 GPS 42 mm Aluminium Case with Sport Band'),
   (self.row('iPad 11th gen (A16) 128GB WiFi','tablet',None,128),'Apple 2025 iPad (A16) 128 GB ROM 11 inch with Wi-Fi Only'),
   (self.row('iPad 9th gen 64GB WiFi','tablet',None,64),'Apple iPad (9th Gen) 64 GB ROM 10.2 inch with Wi-Fi Only A13 Bionic Chip (Space Grey)'),
   (self.row('OnePlus Pad 2 8/128GB','tablet',8,128),'OnePlus Pad 2 30.73 cm (12.1 inch) 8 GB RAM, 128 GB, Wi-Fi Tablet'),
  ]
  for row,title in cases:
   with self.subTest(title=title):self.assertIsNone(identity_problem(row,title))

if __name__=='__main__':unittest.main()
