"""Price identity, stock, fee and non-depreciation regressions on saved receipts."""
import copy, gzip, json, unittest
from pathlib import Path
import _market_refresh_runner as m
import _research_reliance_prices as reliance

WORK=Path(__file__).parent/'_test_fixtures'
class Collectors(unittest.TestCase):
 def test_full_scope_keeps_old_budget_nonphone_and_all_variants(self):
  db={'_meta':{},'old':{'display_name':'Old Phone 4GB/64GB','tier':'D','launch_date':'2011-01-01','discontinued':True},'big':{'display_name':'Old Phone 4GB/128GB','tier':'D'},'tablet':{'display_name':'Tablet 256GB WiFi','tier':'A','category':'tablet'},'import':{'display_name':'Import 128GB','tier':'A','international':True}}
  scope=m.catalogue_scope(db)
  self.assertEqual({x['key'] for x in scope['models']},{'old','big','tablet'})
  self.assertEqual([x['key'] for x in scope['derived_models']],['import'])
  rows=[{'key':x['key'],'new_price_status':'unavailable','note':'Exact source unavailable','new_price_checks':[{'source_url':'https://example.com/product','observed_at':'2026-10-08T00:00:00Z','outcome':'out of stock'}]} for x in scope['models']]
  self.assertEqual(m.validate_scope_coverage({'models':rows},db)['price_coverage'],'partial')
  for invalid in [rows[:-1],rows+[rows[0]],[dict(rows[0],new_price_checks=[])]+rows[1:]]:
   with self.assertRaises(ValueError):m.validate_scope_coverage({'models':invalid},db)
 def test_actual_catalogue_has_no_silent_exclusions(self):
  db=json.loads((Path(__file__).parent/'phone_db.json').read_text());scope=m.catalogue_scope(db)
  keys=[x['key'] for x in scope['models']+scope['derived_models']]
  self.assertEqual(set(keys),set(db)-{'_meta'})
  self.assertEqual(len(keys),len(set(keys)))
 def test_writer_rejects_a_sample_by_default(self):
  from _apply_market_observations import build
  from datetime import datetime,timezone
  db={'_meta':{},'a':{'display_name':'Phone 64GB','tier':'D'}}
  with self.assertRaisesRegex(ValueError,'coverage mismatch'):build({'models':[]},db,datetime.now(timezone.utc))
 def test_chipset_alias_is_exact(self):
  expected=m.norm('Samsung Galaxy S25')
  self.assertTrue(m.family_match(expected,m.norm('Samsung Galaxy S25 5G Snapdragon')))
  for wrong in ['Samsung Galaxy S25 FE Snapdragon','Samsung Galaxy S25 Plus Snapdragon','Samsung Galaxy S25 4G Snapdragon','Samsung Galaxy S25 Exynos','Samsung Galaxy S24 Snapdragon']:
   self.assertFalse(m.family_match(expected,m.norm(wrong)))
 def test_current_retail_does_not_repeat_launch_age(self):
  for year in ['2020','2023','2026']:
   self.assertEqual(m.resale_retail_allowance({'display_name':'Samsung Galaxy S23','tier':'A','launch_date':year+'-01-01'}),.10)
  self.assertEqual(m.resale_retail_allowance({'display_name':'Samsung Galaxy Z Fold 6','tier':'S'}),.15)
  self.assertEqual(m.resale_retail_allowance({'display_name':'Budget phone','tier':'D'}),.15)
 def test_reliance_stock_variant_and_fees(self):
  meta=json.loads((WORK/'reliance_s25_meta.json').read_text());raw=(WORK/'reliance_s25.html').read_text()
  row={'family':'Samsung Galaxy S25','display_name':'Samsung Galaxy S25 256GB','storage':256,'ram':12}
  self.assertEqual(reliance.parse(raw,meta,row)['status'],'verified')
  self.assertEqual(reliance.parse(raw,meta,dict(row,storage=512))['status'],'unverified')
  self.assertEqual(reliance.parse(raw,meta,dict(row,ram=8))['status'],'unverified')
  self.assertEqual(reliance.parse(raw.replace('/InStock','/OutOfStock'),meta,row)['status'],'unavailable')
  self.assertEqual(reliance.parse(raw.replace('/NewCondition','/RefurbishedCondition'),meta,row)['status'],'unverified')
  self.assertEqual(reliance.parse(raw.replace('Free Shipping','Shipping pending'),meta,row)['status'],'unverified')
  self.assertEqual(reliance.parse(raw+'<p>Platform fee ₹99</p>',meta,row)['status'],'unverified')

if __name__=='__main__':unittest.main()
