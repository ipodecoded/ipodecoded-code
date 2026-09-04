import unittest
import json
from datetime import date, datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.db import Base, IPO, IPOGMP, IPOSource, SourceHealth, PipelineRun
from backend.main import app
from pipeline.models import NormalizedIPO, NormalizedGMP
from pipeline.validator import DataValidator
from pipeline.cross_validator import CrossValidator
from pipeline.upsert import upsert_reconciled_ipo, upsert_ipo, upsert_gmp


class TestMultiSourceValidator(unittest.TestCase):
    def test_clean_company_name_corporate_suffixes(self):
        self.assertEqual(DataValidator.clean_company_name("Afcons Infrastructure Limited"), "Afcons Infrastructure")
        self.assertEqual(DataValidator.clean_company_name("Afcons Infrastructure Ltd"), "Afcons Infrastructure")
        self.assertEqual(DataValidator.clean_company_name("Afcons Infrastructure Ltd IPO"), "Afcons Infrastructure")
        self.assertEqual(DataValidator.clean_company_name("Afcons Infrastructure Limited IPO"), "Afcons Infrastructure")
        self.assertEqual(DataValidator.clean_company_name("Auronext Pharma (SME)"), "Auronext Pharma")
        self.assertEqual(DataValidator.clean_company_name("Auronext Pharma Ltd (SME) IPO"), "Auronext Pharma")
        self.assertEqual(DataValidator.clean_company_name("Tata Technologies Limited"), "Tata Technologies")


class TestCrossValidator(unittest.TestCase):
    def test_nse_official_precedence_and_enrichment(self):
        # NSE Record (Official exchange)
        nse_item = NormalizedIPO(
            company_name="Swiggy",
            slug="swiggy-ipo",
            ipo_type="Mainboard",
            status="Open",
            open_date=date(2026, 11, 6),
            close_date=date(2026, 11, 8),
            price_band_low=371.0,
            price_band_high=390.0,
            source_name="NSE",
            source_url="https://www.nseindia.com/api/ipo-current-issue",
            source_id="SWIGGY",
            symbol="SWIGGY"
        )

        # Chittorgarh Record (Has different dates, but has rich issue_size and description)
        chit_item = NormalizedIPO(
            company_name="Swiggy Limited",
            slug="swiggy-limited-ipo",
            ipo_type="Mainboard",
            status="Open",
            open_date=date(2026, 11, 5),  # Discrepant date!
            close_date=date(2026, 11, 8),
            price_band_low=371.0,
            price_band_high=390.0,
            issue_size=11327.43,
            fresh_issue=4499.0,
            ofs=6828.43,
            company_description="Food delivery and quick commerce major.",
            source_name="Chittorgarh",
            source_url="https://www.chittorgarh.com/ipo/swiggy-ipo/1800/",
            source_id="swiggy-ipo"
        )

        reconciled, conflicts = CrossValidator.reconcile(
            nse_items=[nse_item],
            chittorgarh_items=[chit_item],
            investorgain_items=[],
            ipowatch_items=[]
        )

        self.assertEqual(len(reconciled), 1)
        res = reconciled[0]
        canonical = res["canonical"]

        # NSE takes precedence on open_date
        self.assertEqual(canonical.open_date, date(2026, 11, 6))

        # Conflict must be recorded
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["field"], "open_date")
        self.assertEqual(conflicts[0]["source_1"], "NSE")
        self.assertEqual(conflicts[0]["source_2"], "Chittorgarh")
        self.assertEqual(conflicts[0]["resolution"], "NSE_OFFICIAL_PRECEDENCE")

        # Chittorgarh enriched secondary fields
        self.assertEqual(canonical.issue_size, 11327.43)
        self.assertEqual(canonical.fresh_issue, 4499.0)
        self.assertEqual(canonical.ofs, 6828.43)
        self.assertIn("Food delivery", canonical.company_description)

        # Validation semantics: master data is validated across 2 sources
        self.assertTrue(res["master_data_validated"])
        self.assertFalse(res["gmp_sources_available"])
        self.assertFalse(res["gmp_divergence_alert"])
        self.assertTrue(res["is_cross_validated"])
        self.assertIn("NSE", res["sources_verified"])
        self.assertIn("Chittorgarh", res["sources_verified"])

    def test_dual_gmp_and_divergence_conflict(self):
        ig_item = NormalizedIPO(
            company_name="Acme Solar Holdings",
            slug="acme-solar-holdings-ipo",
            ipo_type="Mainboard",
            source_name="InvestorGain",
            current_gmp=NormalizedGMP(
                gmp=30.0,
                source_name="InvestorGain",
                recorded_at=datetime(2026, 11, 5, 10, 0, tzinfo=timezone.utc)
            )
        )

        # IPOWatch gives 50.0 GMP -> divergence is (50-30)/50 = 40% > 30%
        iw_item = NormalizedIPO(
            company_name="Acme Solar Holdings Limited",
            slug="acme-solar-holdings-ipo",
            ipo_type="Mainboard",
            source_name="IPOWatch",
            current_gmp=NormalizedGMP(
                gmp=50.0,
                source_name="IPOWatch",
                recorded_at=datetime(2026, 11, 5, 10, 30, tzinfo=timezone.utc)
            )
        )

        reconciled, conflicts = CrossValidator.reconcile(
            nse_items=[],
            chittorgarh_items=[],
            investorgain_items=[ig_item],
            ipowatch_items=[iw_item]
        )

        self.assertEqual(len(reconciled), 1)
        res = reconciled[0]

        # Primary GMP must strictly equal InvestorGain
        self.assertEqual(res["gmp_investorgain"], 30.0)
        self.assertEqual(res["canonical"].current_gmp.gmp, 30.0)

        # Secondary GMP must strictly equal IPOWatch
        self.assertEqual(res["gmp_ipowatch"], 50.0)
        self.assertEqual(res["current_gmp_secondary"], 50.0)

        # Spread bounds
        self.assertEqual(res["gmp_spread_low"], 30.0)
        self.assertEqual(res["gmp_spread_high"], 50.0)
        self.assertEqual(res["gmp_spread"], "₹30 – ₹50")

        # Validation semantics: GMP available with divergence alert
        self.assertTrue(res["gmp_sources_available"])
        self.assertTrue(res["gmp_divergence_alert"])

        # Divergence > 30% recorded as conflict
        div_conflicts = [c for c in conflicts if c["field"] == "gmp_divergence"]
        self.assertEqual(len(div_conflicts), 1)
        self.assertEqual(div_conflicts[0]["divergence_percent"], 40.0)

    def test_deterministic_status_classification(self):
        today = date.today()

        # 1. Open Issue
        open_item = NormalizedIPO(
            company_name="Open Company",
            slug="open-company-ipo",
            ipo_type="Mainboard",
            open_date=today - timedelta(days=1),
            close_date=today + timedelta(days=1),
            source_name="NSE"
        )

        # 2. Upcoming Issue
        up_item = NormalizedIPO(
            company_name="Upcoming Company",
            slug="upcoming-company-ipo",
            ipo_type="Mainboard",
            open_date=today + timedelta(days=5),
            close_date=today + timedelta(days=8),
            source_name="NSE"
        )

        # 3. Closed Issue
        closed_item = NormalizedIPO(
            company_name="Closed Company",
            slug="closed-company-ipo",
            ipo_type="Mainboard",
            open_date=today - timedelta(days=10),
            close_date=today - timedelta(days=5),
            listing_date=today + timedelta(days=3),
            source_name="Chittorgarh"
        )

        # 4. Listed Issue
        listed_item = NormalizedIPO(
            company_name="Listed Company",
            slug="listed-company-ipo",
            ipo_type="Mainboard",
            open_date=today - timedelta(days=20),
            close_date=today - timedelta(days=15),
            listing_date=today - timedelta(days=5),
            source_name="Chittorgarh"
        )

        reconciled, _ = CrossValidator.reconcile(
            nse_items=[open_item, up_item],
            chittorgarh_items=[closed_item, listed_item],
            investorgain_items=[],
            ipowatch_items=[]
        )

        status_map = {r["canonical"].company_name: r["canonical"].status for r in reconciled}
        self.assertEqual(status_map["Open Company"], "Open")
        self.assertEqual(status_map["Upcoming Company"], "Upcoming")
        self.assertEqual(status_map["Closed Company"], "Closed")
        self.assertEqual(status_map["Listed Company"], "Listed")


class TestReconciledUpsert(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def test_upsert_reconciled_with_provenance_and_gmp(self):
        now = datetime.now(timezone.utc)
        item = {
            "canonical": NormalizedIPO(
                company_name="Premier Energies",
                slug="premier-energies-ipo",
                ipo_type="Mainboard",
                status="Open",
                price_band_high=450.0,
                source_name="NSE"
            ),
            "gmp_investorgain": 190.0,
            "gmp_ipowatch": 195.0,
            "current_gmp_secondary": 195.0,
            "gmp_spread": "₹190 – ₹195",
            "gmp_spread_low": 190.0,
            "gmp_spread_high": 195.0,
            "master_data_validated": True,
            "gmp_sources_available": True,
            "gmp_divergence_alert": False,
            "is_cross_validated": True,
            "has_conflicts": False,
            "conflicts": [],
            "sources_verified": ["NSE", "Chittorgarh", "InvestorGain", "IPOWatch"],
            "source_provenance": {
                "NSE": {"source_name": "NSE", "source_url": "https://nseindia.com", "source_ipo_id": "PREMIER", "raw_data": {"symbol": "PREMIER"}},
                "InvestorGain": {"source_name": "InvestorGain", "source_url": "https://investorgain.com", "source_ipo_id": "100", "raw_data": {"gmp": 190}},
                "IPOWatch": {"source_name": "IPOWatch", "source_url": "https://ipowatch.in", "source_ipo_id": "premier", "raw_data": {"gmp": 195}}
            },
            "gmp_records_to_save": [
                NormalizedGMP(gmp=190.0, source_name="InvestorGain", recorded_at=now),
                NormalizedGMP(gmp=195.0, source_name="IPOWatch", recorded_at=now)
            ]
        }

        ipo_obj, created, updated, gmp_added = upsert_reconciled_ipo(self.db, item)
        self.db.commit()

        self.assertTrue(created)
        self.assertEqual(gmp_added, 2)
        self.assertTrue(ipo_obj.is_cross_validated)
        self.assertTrue(ipo_obj.master_data_validated)
        self.assertTrue(ipo_obj.gmp_sources_available)
        self.assertFalse(ipo_obj.gmp_divergence_alert)

        # Check precise Dual-GMP values in to_dict()
        d = ipo_obj.to_dict()
        self.assertEqual(d["current_gmp"], 190.0)  # Always InvestorGain
        self.assertEqual(d["gmp_investorgain"], 190.0)
        self.assertEqual(d["gmp_ipowatch"], 195.0)
        self.assertEqual(d["current_gmp_secondary"], 195.0)
        self.assertEqual(d["gmp_spread"], "₹190 – ₹195")
        self.assertEqual(d["gmp_spread_low"], 190.0)
        self.assertEqual(d["gmp_spread_high"], 195.0)

        # Check provenance records in ipo_sources table
        sources = self.db.query(IPOSource).filter(IPOSource.ipo_id == ipo_obj.id).all()
        self.assertEqual(len(sources), 3)
        source_names = {s.source_name for s in sources}
        self.assertEqual(source_names, {"NSE", "InvestorGain", "IPOWatch"})

        # Check GMP history records in ipo_gmp table
        gmp_records = self.db.query(IPOGMP).filter(IPOGMP.ipo_id == ipo_obj.id).all()
        self.assertEqual(len(gmp_records), 2)

    def test_gmp_history_multi_day_and_duplicate_prevention(self):
        now = datetime.now(timezone.utc)
        ipo_item = NormalizedIPO(
            company_name="History Test Corp",
            slug="history-test-corp-ipo",
            ipo_type="Mainboard",
            status="Open",
            price_band_high=100.0,
            source_name="NSE"
        )
        ipo_obj, _, _ = upsert_ipo(self.db, ipo_item)
        self.db.commit()

        # Day 1: First observation (₹20 from InvestorGain)
        day1_time = now - timedelta(days=2)
        rec1, created1 = upsert_gmp(self.db, ipo_obj, NormalizedGMP(gmp=20.0, source_name="InvestorGain", recorded_at=day1_time))
        self.assertTrue(created1)

        # Day 1: Same day, same GMP (₹20) -> should be skipped as duplicate
        rec1_dup, created1_dup = upsert_gmp(self.db, ipo_obj, NormalizedGMP(gmp=20.0, source_name="InvestorGain", recorded_at=day1_time))
        self.assertFalse(created1_dup)

        # Day 1: Same day, changed GMP (₹25) -> should create new intra-day record
        rec1_change, created1_change = upsert_gmp(self.db, ipo_obj, NormalizedGMP(gmp=25.0, source_name="InvestorGain", recorded_at=day1_time + timedelta(hours=3)))
        self.assertTrue(created1_change)

        # Day 2: Next day, same GMP (₹25) -> should create new daily observation
        day2_time = now - timedelta(days=1)
        rec2, created2 = upsert_gmp(self.db, ipo_obj, NormalizedGMP(gmp=25.0, source_name="InvestorGain", recorded_at=day2_time))
        self.assertTrue(created2)

        # Total records for InvestorGain should be 3 (Day1 morning, Day1 afternoon change, Day2 daily observation)
        ig_records = self.db.query(IPOGMP).filter(IPOGMP.ipo_id == ipo_obj.id, IPOGMP.source_name == "InvestorGain").all()
        self.assertEqual(len(ig_records), 3)


class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "IPODecoded API")
        self.assertIn("endpoints", data)

    def test_sources_health_endpoint(self):
        res = self.client.get("/api/sources/health")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_pipeline_conflicts_endpoint(self):
        res = self.client.get("/api/pipeline/conflicts")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("conflicts", data)

    def test_pipeline_runs_endpoint(self):
        res = self.client.get("/api/pipeline/runs")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_scheduler_status_endpoint(self):
        res = self.client.get("/api/scheduler/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("is_running", data)
        self.assertIn("interval_hours", data)
        self.assertIn("jobs", data)

    def test_sitemap_endpoint(self):
        res = self.client.get("/api/sitemap.xml")
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/xml", res.headers.get("content-type", ""))
        self.assertIn("<urlset", res.text)
        self.assertIn("https://ipodecoded.journaldecoded.in", res.text)


if __name__ == "__main__":
    unittest.main()
