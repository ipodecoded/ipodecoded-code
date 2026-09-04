import unittest
from datetime import date, datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db import Base, IPO, IPOGMP
from pipeline.models import NormalizedIPO, NormalizedGMP
from pipeline.validator import DataValidator
from pipeline.upsert import upsert_ipo, upsert_gmp, safe_update_field

class TestDataValidator(unittest.TestCase):
    def test_clean_company_name(self):
        self.assertEqual(DataValidator.clean_company_name("Tata Tech IPO"), "Tata Tech")
        self.assertEqual(DataValidator.clean_company_name("  Bajaj Housing Finance  "), "Bajaj Housing Finance")

    def test_parse_indian_date(self):
        d1 = DataValidator.parse_indian_date("10 Sep 2026")
        self.assertEqual(d1, date(2026, 9, 10))

        d2 = DataValidator.parse_indian_date("10-09-2026")
        self.assertEqual(d2, date(2026, 9, 10))

        d3 = DataValidator.parse_indian_date("Sep 10, 2026")
        self.assertEqual(d3, date(2026, 9, 10))

        d4 = DataValidator.parse_indian_date("TBA")
        self.assertIsNone(d4)

    def test_parse_price_band(self):
        low, high = DataValidator.parse_price_band("₹450 to ₹475")
        self.assertEqual((low, high), (450.0, 475.0))

        low, high = DataValidator.parse_price_band("100")
        self.assertEqual((low, high), (100.0, 100.0))

    def test_validate_ipo_valid(self):
        ipo = NormalizedIPO(
            company_name="Sample Tech",
            slug="sample-tech-ipo",
            price_band_low=100.0,
            price_band_high=110.0,
            lot_size=100
        )
        self.assertTrue(DataValidator.validate_ipo(ipo))
        self.assertEqual(ipo.minimum_investment, 11000.0)

    def test_validate_ipo_invalid(self):
        ipo = NormalizedIPO(
            company_name="",
            slug="bad-ipo"
        )
        self.assertFalse(DataValidator.validate_ipo(ipo))


class TestIdempotencyAndHistory(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def test_safe_update_does_not_overwrite_with_none(self):
        existing = "Official SEBI Prospectus"
        new_val = None
        val, changed = safe_update_field(existing, new_val)
        self.assertEqual(val, existing)
        self.assertFalse(changed)

    def test_upsert_idempotency(self):
        ipo_data = NormalizedIPO(
            company_name="Test Company",
            slug="test-company-ipo",
            ipo_type="Mainboard",
            status="Upcoming",
            price_band_low=200.0,
            price_band_high=220.0,
            lot_size=50
        )

        # 1. First insert
        ipo_obj, created, updated = upsert_ipo(self.db, ipo_data)
        self.db.commit()
        self.assertTrue(created)
        self.assertFalse(updated)

        total_count = self.db.query(IPO).count()
        self.assertEqual(total_count, 1)

        # 2. Second insert with identical data -> Idempotent!
        ipo_obj2, created2, updated2 = upsert_ipo(self.db, ipo_data)
        self.db.commit()
        self.assertFalse(created2)
        self.assertFalse(updated2)

        total_count_after = self.db.query(IPO).count()
        self.assertEqual(total_count_after, 1)

    def test_change_detection(self):
        ipo_data = NormalizedIPO(
            company_name="Test Company",
            slug="test-company-ipo",
            price_band_low=200.0,
            price_band_high=220.0
        )
        ipo_obj, _, _ = upsert_ipo(self.db, ipo_data)
        self.db.commit()

        # Update price band
        modified_data = NormalizedIPO(
            company_name="Test Company",
            slug="test-company-ipo",
            price_band_low=210.0,
            price_band_high=230.0
        )
        ipo_obj2, created, updated = upsert_ipo(self.db, modified_data)
        self.db.commit()

        self.assertFalse(created)
        self.assertTrue(updated)
        self.assertEqual(float(ipo_obj2.price_band_high), 230.0)

    def test_gmp_history_tracking(self):
        ipo_data = NormalizedIPO(
            company_name="Test Company",
            slug="test-company-ipo",
            price_band_high=500.0
        )
        ipo_obj, _, _ = upsert_ipo(self.db, ipo_data)
        self.db.commit()

        now = datetime.now(timezone.utc)

        # Day 1: GMP = 50
        gmp1 = NormalizedGMP(gmp=50.0, source_name="Source A", recorded_at=now - timedelta(days=2))
        rec1, created1 = upsert_gmp(self.db, ipo_obj, gmp1)
        self.db.commit()
        self.assertTrue(created1)
        self.assertEqual(float(rec1.estimated_listing_price), 550.0)
        self.assertEqual(float(rec1.estimated_gain_percent), 10.0)

        # Repeated same GMP: should NOT insert duplicate
        rec_same, created_same = upsert_gmp(self.db, ipo_obj, gmp1)
        self.db.commit()
        self.assertFalse(created_same)

        # Day 2: GMP changes to 65 -> should insert new historical record
        gmp2 = NormalizedGMP(gmp=65.0, source_name="Source A", recorded_at=now - timedelta(days=1))
        rec2, created2 = upsert_gmp(self.db, ipo_obj, gmp2)
        self.db.commit()
        self.assertTrue(created2)

        # Verify history preservation
        all_records = self.db.query(IPOGMP).filter(IPOGMP.ipo_id == ipo_obj.id).all()
        self.assertEqual(len(all_records), 2)
        self.assertEqual([float(r.gmp) for r in all_records], [50.0, 65.0])


class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        self.client = TestClient(app)

    def test_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertIn("healthy", res.json()["status"])

    def test_stats(self):
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_active_ipos", data)

    def test_ipos_list(self):
        res = self.client.get("/api/ipos")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total"], 1)

    def test_ipo_detail_and_gmp_history(self):
        res_list = self.client.get("/api/ipos")
        self.assertEqual(res_list.status_code, 200)
        items = res_list.json()["items"]
        self.assertGreater(len(items), 0)
        slug = items[0]["slug"]

        res = self.client.get(f"/api/ipos/{slug}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["slug"], slug)

        res_gmp = self.client.get(f"/api/ipos/{slug}/gmp-history")
        self.assertEqual(res_gmp.status_code, 200)
        self.assertIsInstance(res_gmp.json(), list)


if __name__ == "__main__":
    unittest.main()
