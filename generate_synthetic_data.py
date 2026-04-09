import argparse
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sample_data"
DB_PATH = DATA_DIR / "researcher_demo.db"


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat() + "Z"


def recreate_db(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate synthetic hackathon data for The Researcher.")
    parser.add_argument("--customers", type=int, default=8)
    args = parser.parse_args()

    random.seed(7)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    recreate_db(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE customers (customer_id TEXT PRIMARY KEY, customer_name TEXT, age INTEGER, address TEXT, country TEXT, occupation TEXT, business_type TEXT, risk_level TEXT, kyc_status TEXT, onboarding_date TEXT, account_opened_date TEXT, pep_match INTEGER, sanctions_match INTEGER);
        CREATE TABLE onboarding_docs (customer_id TEXT, doc_type TEXT, doc_id TEXT, verified INTEGER);
        CREATE TABLE accounts (account_id TEXT PRIMARY KEY, customer_id TEXT, account_type TEXT, status TEXT, balance REAL, currency TEXT);
        CREATE TABLE transactions (transaction_id TEXT PRIMARY KEY, customer_id TEXT, origin_account TEXT, destination_account TEXT, beneficiary_name TEXT, destination_country TEXT, channel TEXT, amount REAL, currency TEXT, timestamp TEXT);
        CREATE TABLE logins (login_id TEXT PRIMARY KEY, customer_id TEXT, ip_address TEXT, country TEXT, city TEXT, device_id TEXT, login_timestamp TEXT);
        CREATE TABLE devices (device_id TEXT PRIMARY KEY, customer_id TEXT, browser TEXT, os TEXT, emulator_flag INTEGER, rooted_flag INTEGER, fingerprint_confidence REAL, first_seen TEXT, last_seen TEXT);
        CREATE TABLE device_account_links (device_id TEXT, customer_id TEXT);
        CREATE TABLE entity_links (entity_type TEXT, entity_value TEXT, customer_id TEXT, linked_account_id TEXT);
        CREATE TABLE cases (case_id TEXT PRIMARY KEY, customer_id TEXT, transaction_id TEXT, status TEXT, disposition TEXT, sar_filed INTEGER, analyst_note TEXT, created_at TEXT);
        """
    )

    cities = [("Mumbai", "IN"), ("Delhi", "IN"), ("Dubai", "AE"), ("Singapore", "SG")]
    occupations = ["Consultant", "Trader", "Developer", "Importer"]
    businesses = ["Sole Proprietorship", "LLC", "Freelancer", "Retail"]

    shared_email = "x@example.com"
    shared_phone = "+919999999999"
    suspicious_device = "DEV-44"
    now = datetime(2026, 4, 9, 10, 15, 0)

    alert_customer_id = "CUST001"
    transaction_id = "TXN555"

    for i in range(1, args.customers + 1):
        customer_id = f"CUST{i:03d}"
        account_id = f"ACC{i:04d}"
        device_id = suspicious_device if i <= 4 else f"DEV-{i:02d}"
        city, country = cities[0 if i <= 2 else min(i % len(cities), len(cities) - 1)]
        email = shared_email if i <= 3 else f"user{i}@example.com"
        phone = shared_phone if i <= 2 else f"+919999990{i:03d}"
        address = "Mumbai, Maharashtra, India" if i <= 2 else f"{city}, {country}"

        cur.execute(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                customer_id,
                f"Customer {i}",
                random.randint(24, 52),
                address,
                country,
                random.choice(occupations),
                random.choice(businesses),
                "medium" if i == 1 else "low",
                "verified",
                iso(now - timedelta(days=390 + i)),
                iso(now - timedelta(days=390 + i)),
                0,
                0,
            ),
        )
        cur.executemany(
            "INSERT INTO onboarding_docs VALUES (?, ?, ?, ?)",
            [
                (customer_id, "PAN", f"PAN-{i:04d}", 1),
                (customer_id, "AADHAAR", f"AADHAAR-{i:04d}", 1),
            ],
        )
        cur.execute(
            "INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)",
            (account_id, customer_id, "checking", "active", float(random.randint(20000, 150000)), "INR"),
        )
        existing_device = cur.execute("SELECT 1 FROM devices WHERE device_id = ?", (device_id,)).fetchone()
        if not existing_device:
            cur.execute(
                "INSERT INTO devices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (device_id, customer_id, "Chrome 124", "Android 15", 0, 0, 0.95, iso(now - timedelta(days=90)), iso(now - timedelta(hours=2))),
            )
        cur.execute("INSERT INTO device_account_links VALUES (?, ?)", (device_id, customer_id))
        cur.executemany(
            "INSERT INTO entity_links VALUES (?, ?, ?, ?)",
            [
                ("email", email, customer_id, account_id),
                ("phone", phone, customer_id, account_id),
                ("address", address, customer_id, account_id),
                ("device", device_id, customer_id, account_id),
            ],
        )

        if customer_id == alert_customer_id:
            cur.executemany(
                "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (transaction_id, customer_id, account_id, "BEN9001", "Al Noor Trading LLC", "AE", "mobile_app", 9500.0, "USD", iso(now - timedelta(minutes=30))),
                    ("TXN554", customer_id, account_id, "BEN7001", "SK Exports", "IN", "web", 2200.0, "USD", iso(now - timedelta(days=1))),
                    ("TXN553", customer_id, account_id, "BEN6001", "R K Holdings", "IN", "mobile_app", 300000.0, "INR", iso(now - timedelta(days=2))),
                ],
            )
            cur.executemany(
                "INSERT INTO logins VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    ("LOG100", customer_id, "49.36.22.1", "IN", "Mumbai", suspicious_device, iso(now - timedelta(hours=4))),
                    ("LOG101", customer_id, "185.220.101.1", "AE", "Dubai", suspicious_device, iso(now - timedelta(hours=2, minutes=5))),
                    ("LOG102", customer_id, "49.36.22.1", "IN", "Mumbai", suspicious_device, iso(now - timedelta(days=1))),
                ],
            )
            cur.executemany(
                "INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    ("CASE101", customer_id, "TXN553", "closed", "monitor", 0, "Reviewed for unusual outbound transfer; activity continued under enhanced monitoring.", iso(now - timedelta(days=35))),
                    ("CASE099", customer_id, "TXN554", "closed", "clear", 0, "Customer explanation accepted after invoice review.", iso(now - timedelta(days=57))),
                ],
            )
        else:
            cur.execute(
                "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (f"TXN{i:03d}", customer_id, account_id, f"BEN{i:04d}", f"Beneficiary {i}", country, "mobile_app", float(random.randint(500, 5000)), "INR", iso(now - timedelta(days=i))),
            )
            cur.execute(
                "INSERT INTO logins VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f"LOG{i:03d}", customer_id, "49.36.22.1", country, city, device_id, iso(now - timedelta(days=i))),
            )

    conn.commit()
    conn.close()

    internal_seed = {
        "case_annotations": {
            "CUST001": {
                "customer_id": "CUST001",
                "analyst_watchlist": False,
                "recent_profile_changes": [
                    {
                        "field": "address",
                        "changed_at": "2026-04-02T10:20:00Z",
                        "old_value": "Pune, Maharashtra, India",
                        "new_value": "Mumbai, Maharashtra, India"
                    }
                ],
                "adverse_media_hits": []
            }
        },
        "ip_intelligence": {
            "49.36.22.1": {"vpn_suspected": False, "proxy_score": 0.04, "tor_exit_node": False, "asn_name": "Jio Broadband"},
            "185.220.101.1": {"vpn_suspected": True, "proxy_score": 0.91, "tor_exit_node": True, "asn_name": "Anonymous Proxy Network"}
        },
        "device_risk": {
            "DEV-44": {"device_id": "DEV-44", "mule_association_count": 4, "fraud_cluster_score": 0.86, "is_emulator_like": False}
        }
    }
    (DATA_DIR / "internal_api_data.json").write_text(json.dumps(internal_seed, indent=2), encoding="utf-8")

    alert = {
        "case_metadata": {
            "case_id": "CASE123",
            "alert_id": "ALT789",
            "customer_id": "CUST001",
            "transaction_id": "TXN555",
            "created_at": iso(now)
        },
        "trigger_source": "the_sentry",
        "alert_summary": {
            "alert_type": "cross_border_velocity",
            "risk_score": 0.91,
            "model_name": "sentry_gradient_boost_v3",
            "model_version": "3.2.1",
            "anomaly_band": "high",
            "reason_codes": [
                {"code": "CROSS_BORDER_SPIKE", "description": "Rapid increase in cross-border transfer activity."},
                {"code": "VELOCITY_SPIKE", "description": "Transaction velocity exceeded customer baseline."}
            ]
        },
        "trigger_context": {
            "current_ip": "185.220.101.1",
            "current_ip_country": "AE",
            "device_id": "DEV-44",
            "shared_email": "x@example.com",
            "shared_phone": "+919999999999",
            "channel": "mobile_app"
        },
        "flagged_transaction": {
            "origin_account": "ACC0001",
            "destination_account": "BEN9001",
            "amount": 9500.0,
            "currency": "USD",
            "timestamp": iso(now - timedelta(minutes=30)),
            "destination_country": "AE"
        }
    }
    (DATA_DIR / "sample_sentry_alert.json").write_text(json.dumps(alert, indent=2), encoding="utf-8")
    print(f"Synthetic data regenerated in {DATA_DIR}")


if __name__ == "__main__":
    main()
