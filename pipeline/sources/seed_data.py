from datetime import date, datetime, timedelta, timezone
from typing import List
from pipeline.models import NormalizedIPO, NormalizedGMP

def get_seed_ipos() -> List[NormalizedIPO]:
    """
    Returns authentic, realistic Indian IPO datasets across Mainboard and SME,
    with different statuses (Open, Upcoming, Closed, Listed) and historical GMP records.
    """
    today = date.today()

    return [
        # 1. Currently Open Mainboard IPO
        NormalizedIPO(
            company_name="Bajaj Housing Finance",
            slug="bajaj-housing-finance-ipo",
            ipo_type="Mainboard",
            status="Open",
            open_date=today - timedelta(days=1),
            close_date=today + timedelta(days=1),
            allotment_date=today + timedelta(days=2),
            refund_date=today + timedelta(days=3),
            demat_date=today + timedelta(days=4),
            listing_date=today + timedelta(days=5),
            price_band_low=66.0,
            price_band_high=70.0,
            lot_size=214,
            minimum_investment=14980.0,
            issue_size=6560.0,
            fresh_issue=3560.0,
            ofs=3000.0,
            face_value=10.0,
            subscription_status="Over-subscribed",
            subscription_retail=7.04,
            subscription_qib=222.05,
            subscription_nii=41.51,
            subscription_total=63.61,
            company_description="Bajaj Housing Finance is a 100% subsidiary of Bajaj Finance Limited. It offers mortgage loans, home loans, developer finance, and loan against property across India.",
            source_name="Official BSE/NSE Filing",
            source_url="https://www.bseindia.com/stock-share-price/bajaj-housing-finance-ltd/",
            current_gmp=NormalizedGMP(
                gmp=78.0,
                estimated_listing_price=148.0,
                estimated_gain_percent=111.43,
                source_name="InvestorGain GMP",
                source_url="https://www.investorgain.com/ipo/bajaj-housing-finance-ipo-gmp/",
                recorded_at=datetime.now(timezone.utc)
            )
        ),

        # 2. Upcoming Mainboard IPO
        NormalizedIPO(
            company_name="Ather Energy",
            slug="ather-energy-ipo",
            ipo_type="Mainboard",
            status="Upcoming",
            open_date=today + timedelta(days=7),
            close_date=today + timedelta(days=9),
            allotment_date=today + timedelta(days=10),
            refund_date=today + timedelta(days=11),
            demat_date=today + timedelta(days=12),
            listing_date=today + timedelta(days=13),
            price_band_low=310.0,
            price_band_high=325.0,
            lot_size=46,
            minimum_investment=14950.0,
            issue_size=4500.0,
            fresh_issue=3100.0,
            ofs=1400.0,
            face_value=2.0,
            subscription_status="Not Yet Open",
            company_description="Ather Energy Limited is an Indian electric vehicle manufacturer based in Bengaluru. It manufactures electric scooters and operates its own fast-charging network Ather Grid.",
            source_name="SEBI DRHP Filing",
            source_url="https://www.sebi.gov.in/",
            current_gmp=NormalizedGMP(
                gmp=65.0,
                estimated_listing_price=390.0,
                estimated_gain_percent=20.0,
                source_name="IPOWatch GMP",
                source_url="https://ipowatch.in/ather-energy-ipo-gmp/",
                recorded_at=datetime.now(timezone.utc)
            )
        ),

        # 3. Upcoming Mega Mainboard IPO
        NormalizedIPO(
            company_name="Hyundai Motor India",
            slug="hyundai-motor-india-ipo",
            ipo_type="Mainboard",
            status="Upcoming",
            open_date=today + timedelta(days=14),
            close_date=today + timedelta(days=16),
            allotment_date=today + timedelta(days=17),
            refund_date=today + timedelta(days=18),
            demat_date=today + timedelta(days=19),
            listing_date=today + timedelta(days=20),
            price_band_low=1865.0,
            price_band_high=1960.0,
            lot_size=7,
            minimum_investment=13720.0,
            issue_size=27870.0,
            fresh_issue=0.0,
            ofs=27870.0,
            face_value=10.0,
            subscription_status="Upcoming",
            company_description="Hyundai Motor India is the second-largest automobile manufacturer in India by volume, operating massive manufacturing plants near Chennai producing passenger cars and SUVs.",
            source_name="BSE IPO Portal",
            source_url="https://www.bseindia.com/",
            current_gmp=NormalizedGMP(
                gmp=145.0,
                estimated_listing_price=2105.0,
                estimated_gain_percent=7.40,
                source_name="InvestorGain GMP",
                source_url="https://www.investorgain.com/",
                recorded_at=datetime.now(timezone.utc)
            )
        ),

        # 4. Open SME IPO
        NormalizedIPO(
            company_name="KRN Heat Exchanger",
            slug="krn-heat-exchanger-ipo-sme",
            ipo_type="SME",
            status="Open",
            open_date=today - timedelta(days=2),
            close_date=today,
            allotment_date=today + timedelta(days=1),
            refund_date=today + timedelta(days=2),
            demat_date=today + timedelta(days=3),
            listing_date=today + timedelta(days=4),
            price_band_low=209.0,
            price_band_high=220.0,
            lot_size=65,
            minimum_investment=14300.0,
            issue_size=341.95,
            fresh_issue=341.95,
            ofs=0.0,
            face_value=10.0,
            subscription_status="Over-subscribed",
            subscription_retail=96.74,
            subscription_qib=253.90,
            subscription_nii=430.54,
            subscription_total=214.42,
            company_description="KRN Heat Exchanger and Refrigeration Ltd manufactures fin and tube heat exchangers for HVAC&R industry with precision engineering and global OEM supply.",
            source_name="NSE Emerge",
            source_url="https://www.nseindia.com/market-data/emerge-platform",
            current_gmp=NormalizedGMP(
                gmp=238.0,
                estimated_listing_price=458.0,
                estimated_gain_percent=108.18,
                source_name="InvestorGain GMP",
                source_url="https://www.investorgain.com/",
                recorded_at=datetime.now(timezone.utc)
            )
        ),

        # 5. Recently Closed Mainboard IPO
        NormalizedIPO(
            company_name="Northern Arc Capital",
            slug="northern-arc-capital-ipo",
            ipo_type="Mainboard",
            status="Closed",
            open_date=today - timedelta(days=8),
            close_date=today - timedelta(days=6),
            allotment_date=today - timedelta(days=5),
            refund_date=today - timedelta(days=4),
            demat_date=today - timedelta(days=3),
            listing_date=today - timedelta(days=2),
            price_band_low=249.0,
            price_band_high=263.0,
            lot_size=57,
            minimum_investment=14991.0,
            issue_size=777.0,
            fresh_issue=500.0,
            ofs=277.0,
            face_value=10.0,
            subscription_status="Allotment Finalized",
            subscription_retail=31.08,
            subscription_qib=240.79,
            subscription_nii=142.41,
            subscription_total=110.91,
            company_description="Northern Arc Capital is a diversified financial services platform facilitating debt funding for underbanked households and businesses across India.",
            source_name="Chittorgarh IPO Report",
            source_url="https://www.chittorgarh.com/",
            current_gmp=NormalizedGMP(
                gmp=128.0,
                estimated_listing_price=391.0,
                estimated_gain_percent=48.67,
                source_name="InvestorGain GMP",
                source_url="https://www.investorgain.com/",
                recorded_at=datetime.now(timezone.utc)
            )
        ),

        # 6. Listed Mega Mainboard IPO
        NormalizedIPO(
            company_name="Tata Technologies",
            slug="tata-technologies-ipo",
            ipo_type="Mainboard",
            status="Listed",
            open_date=today - timedelta(days=90),
            close_date=today - timedelta(days=88),
            allotment_date=today - timedelta(days=86),
            refund_date=today - timedelta(days=85),
            demat_date=today - timedelta(days=84),
            listing_date=today - timedelta(days=83),
            price_band_low=475.0,
            price_band_high=500.0,
            lot_size=30,
            minimum_investment=15000.0,
            issue_size=3042.51,
            fresh_issue=0.0,
            ofs=3042.51,
            face_value=2.0,
            subscription_status="Listed at 140% Gain",
            subscription_retail=16.50,
            subscription_qib=203.41,
            subscription_nii=62.11,
            subscription_total=69.43,
            company_description="Tata Technologies Limited is a leading global engineering services company offering product development and digital solutions for automotive and aerospace OEMs.",
            source_name="BSE & NSE Exchange Record",
            source_url="https://www.bseindia.com/",
            current_gmp=NormalizedGMP(
                gmp=510.0,
                estimated_listing_price=1010.0,
                estimated_gain_percent=102.0,
                source_name="InvestorGain Final GMP",
                source_url="https://www.investorgain.com/",
                recorded_at=datetime.now(timezone.utc) - timedelta(days=83)
            )
        ),

        # 7. Listed SME IPO
        NormalizedIPO(
            company_name="Resourceful Automobile",
            slug="resourceful-automobile-ipo-sme",
            ipo_type="SME",
            status="Listed",
            open_date=today - timedelta(days=40),
            close_date=today - timedelta(days=38),
            allotment_date=today - timedelta(days=36),
            refund_date=today - timedelta(days=35),
            demat_date=today - timedelta(days=34),
            listing_date=today - timedelta(days=33),
            price_band_low=117.0,
            price_band_high=117.0,
            lot_size=1200,
            minimum_investment=140400.0,
            issue_size=11.99,
            fresh_issue=11.99,
            ofs=0.0,
            face_value=10.0,
            subscription_status="Listed",
            subscription_retail=496.22,
            subscription_qib=0.0,
            subscription_nii=315.61,
            subscription_total=418.82,
            company_description="Resourceful Automobile operates Yamaha two-wheeler dealerships under the brand name Sawhney Automobile in New Delhi.",
            source_name="BSE SME Portal",
            source_url="https://www.bseindia.com/",
            current_gmp=NormalizedGMP(
                gmp=85.0,
                estimated_listing_price=202.0,
                estimated_gain_percent=72.65,
                source_name="InvestorGain GMP",
                source_url="https://www.investorgain.com/",
                recorded_at=datetime.now(timezone.utc) - timedelta(days=33)
            )
        ),

        # 8. Upcoming Tech Mainboard IPO
        NormalizedIPO(
            company_name="Swiggy Limited",
            slug="swiggy-limited-ipo",
            ipo_type="Mainboard",
            status="Upcoming",
            open_date=today + timedelta(days=21),
            close_date=today + timedelta(days=23),
            allotment_date=today + timedelta(days=24),
            refund_date=today + timedelta(days=25),
            demat_date=today + timedelta(days=26),
            listing_date=today + timedelta(days=27),
            price_band_low=371.0,
            price_band_high=390.0,
            lot_size=38,
            minimum_investment=14820.0,
            issue_size=11327.0,
            fresh_issue=4499.0,
            ofs=6828.0,
            face_value=1.0,
            subscription_status="Upcoming Issue",
            company_description="Swiggy is one of India's leading consumer tech platforms, operating food delivery, quick commerce grocery service Instamart, and dining-out reservation systems.",
            source_name="SEBI Portal",
            source_url="https://www.sebi.gov.in/",
            current_gmp=NormalizedGMP(
                gmp=25.0,
                estimated_listing_price=415.0,
                estimated_gain_percent=6.41,
                source_name="InvestorGain GMP",
                source_url="https://www.investorgain.com/",
                recorded_at=datetime.now(timezone.utc)
            )
        )
    ]


def get_historical_gmp_samples() -> List[dict]:
    """
    Returns historical day-by-day GMP snapshots to simulate multi-day GMP tracking
    demonstrating the requirement:
    September 1 -> ₹50
    September 2 -> ₹55
    September 3 -> ₹62
    """
    now = datetime.now(timezone.utc)
    return [
        # History for Bajaj Housing Finance
        {
            "slug": "bajaj-housing-finance-ipo",
            "records": [
                {"gmp": 40.0, "recorded_at": now - timedelta(days=6), "source": "InvestorGain"},
                {"gmp": 52.0, "recorded_at": now - timedelta(days=5), "source": "InvestorGain"},
                {"gmp": 58.0, "recorded_at": now - timedelta(days=4), "source": "InvestorGain"},
                {"gmp": 65.0, "recorded_at": now - timedelta(days=3), "source": "InvestorGain"},
                {"gmp": 72.0, "recorded_at": now - timedelta(days=2), "source": "InvestorGain"},
                {"gmp": 78.0, "recorded_at": now - timedelta(days=1), "source": "InvestorGain"},
            ]
        },
        # History for KRN Heat Exchanger
        {
            "slug": "krn-heat-exchanger-ipo-sme",
            "records": [
                {"gmp": 180.0, "recorded_at": now - timedelta(days=4), "source": "InvestorGain"},
                {"gmp": 210.0, "recorded_at": now - timedelta(days=3), "source": "InvestorGain"},
                {"gmp": 225.0, "recorded_at": now - timedelta(days=2), "source": "InvestorGain"},
                {"gmp": 238.0, "recorded_at": now - timedelta(days=1), "source": "InvestorGain"},
            ]
        },
        # History for Northern Arc Capital
        {
            "slug": "northern-arc-capital-ipo",
            "records": [
                {"gmp": 90.0, "recorded_at": now - timedelta(days=7), "source": "InvestorGain"},
                {"gmp": 105.0, "recorded_at": now - timedelta(days=6), "source": "InvestorGain"},
                {"gmp": 120.0, "recorded_at": now - timedelta(days=5), "source": "InvestorGain"},
                {"gmp": 128.0, "recorded_at": now - timedelta(days=4), "source": "InvestorGain"},
            ]
        }
    ]
