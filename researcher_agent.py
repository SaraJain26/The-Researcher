import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sample_data"
DB_PATH = DATA_DIR / "researcher_demo.db"
INTERNAL_API_DATA_PATH = DATA_DIR / "internal_api_data.json"


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def http_get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def ensure_demo_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            customer_name TEXT,
            age INTEGER,
            address TEXT,
            country TEXT,
            occupation TEXT,
            business_type TEXT,
            risk_level TEXT,
            kyc_status TEXT,
            onboarding_date TEXT,
            account_opened_date TEXT,
            pep_match INTEGER,
            sanctions_match INTEGER
        );

        CREATE TABLE IF NOT EXISTS onboarding_docs (
            customer_id TEXT,
            doc_type TEXT,
            doc_id TEXT,
            verified INTEGER
        );

        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT,
            account_type TEXT,
            status TEXT,
            balance REAL,
            currency TEXT
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            customer_id TEXT,
            origin_account TEXT,
            destination_account TEXT,
            beneficiary_name TEXT,
            destination_country TEXT,
            channel TEXT,
            amount REAL,
            currency TEXT,
            timestamp TEXT
        );

        CREATE TABLE IF NOT EXISTS logins (
            login_id TEXT PRIMARY KEY,
            customer_id TEXT,
            ip_address TEXT,
            country TEXT,
            city TEXT,
            device_id TEXT,
            login_timestamp TEXT
        );

        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            customer_id TEXT,
            browser TEXT,
            os TEXT,
            emulator_flag INTEGER,
            rooted_flag INTEGER,
            fingerprint_confidence REAL,
            first_seen TEXT,
            last_seen TEXT
        );

        CREATE TABLE IF NOT EXISTS device_account_links (
            device_id TEXT,
            customer_id TEXT
        );

        CREATE TABLE IF NOT EXISTS entity_links (
            entity_type TEXT,
            entity_value TEXT,
            customer_id TEXT,
            linked_account_id TEXT
        );

        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY,
            customer_id TEXT,
            transaction_id TEXT,
            status TEXT,
            disposition TEXT,
            sar_filed INTEGER,
            analyst_note TEXT,
            created_at TEXT
        );
        """
    )

    existing = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    if existing:
        conn.close()
        return

    cur.execute(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "CUST001",
            "Rahul Sharma",
            34,
            "Mumbai, Maharashtra, India",
            "IN",
            "Consultant",
            "Sole Proprietorship",
            "medium",
            "verified",
            "2025-03-15T09:00:00Z",
            "2025-03-15T09:00:00Z",
            0,
            0,
        ),
    )

    cur.executemany(
        "INSERT INTO onboarding_docs VALUES (?, ?, ?, ?)",
        [
            ("CUST001", "PAN", "PAN-9981", 1),
            ("CUST001", "AADHAAR", "AADHAAR-8821", 1),
            ("CUST001", "SELFIE_CHECK", "SELFIE-1001", 1),
        ],
    )

    cur.executemany(
        "INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("ACC1001", "CUST001", "checking", "active", 125000.0, "INR"),
            ("ACC2001", "CUST001", "forex", "active", 8400.0, "USD"),
        ],
    )

    cur.executemany(
        "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("TXN555", "CUST001", "ACC2001", "BEN9001", "Al Noor Trading LLC", "AE", "mobile_app", 9500.0, "USD", "2026-04-09T09:45:00Z"),
            ("TXN554", "CUST001", "ACC2001", "BEN7001", "SK Exports", "IN", "web", 2200.0, "USD", "2026-04-08T13:30:00Z"),
            ("TXN553", "CUST001", "ACC1001", "BEN6001", "R K Holdings", "IN", "mobile_app", 300000.0, "INR", "2026-04-07T11:15:00Z"),
        ],
    )

    cur.executemany(
        "INSERT INTO logins VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("LOG100", "CUST001", "49.36.22.1", "IN", "Mumbai", "DEV-44", "2026-04-09T06:15:00Z"),
            ("LOG101", "CUST001", "185.220.101.1", "AE", "Dubai", "DEV-44", "2026-04-09T08:10:00Z"),
            ("LOG102", "CUST001", "49.36.22.1", "IN", "Mumbai", "DEV-44", "2026-04-08T10:15:00Z"),
        ],
    )

    cur.executemany(
        "INSERT INTO devices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [("DEV-44", "CUST001", "Chrome 124", "Android 15", 0, 0, 0.97, "2026-01-10T07:00:00Z", "2026-04-09T08:10:00Z")],
    )

    cur.executemany(
        "INSERT INTO device_account_links VALUES (?, ?)",
        [("DEV-44", "CUST001"), ("DEV-44", "CUST778"), ("DEV-44", "CUST779"), ("DEV-44", "CUST780")],
    )

    cur.executemany(
        "INSERT INTO entity_links VALUES (?, ?, ?, ?)",
        [
            ("email", "x@example.com", "CUST001", "ACC1001"),
            ("email", "x@example.com", "CUST778", "ACC7711"),
            ("email", "x@example.com", "CUST779", "ACC7712"),
            ("phone", "+919999999999", "CUST001", "ACC1001"),
            ("phone", "+919999999999", "CUST500", "ACC5001"),
            ("address", "Mumbai, Maharashtra, India", "CUST001", "ACC1001"),
            ("address", "Mumbai, Maharashtra, India", "CUST411", "ACC4111"),
            ("device", "DEV-44", "CUST001", "ACC1001"),
            ("device", "DEV-44", "CUST778", "ACC7711"),
            ("device", "DEV-44", "CUST779", "ACC7712"),
            ("device", "DEV-44", "CUST780", "ACC7713"),
        ],
    )

    cur.executemany(
        "INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("CASE101", "CUST001", "TXN553", "closed", "monitor", 0, "Reviewed for unusual outbound transfer; activity continued under enhanced monitoring.", "2026-03-01T11:00:00Z"),
            ("CASE099", "CUST001", "TXN554", "closed", "clear", 0, "Customer explanation accepted after invoice review.", "2026-02-12T14:30:00Z"),
        ],
    )

    conn.commit()
    conn.close()


@dataclass
class SQLTools:
    db_path: Path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


class InternalAPIConnectors:
    def get_case_annotations(self, customer_id: str) -> Dict[str, Any]:
        return {
            "customer_id": customer_id,
            "analyst_watchlist": False,
            "recent_profile_changes": [
                {
                    "field": "address",
                    "changed_at": "2026-04-02T10:20:00Z",
                    "old_value": "Pune, Maharashtra, India",
                    "new_value": "Mumbai, Maharashtra, India",
                }
            ],
            "adverse_media_hits": [],
        }

    def get_ip_intelligence(self, ip_address: str) -> Dict[str, Any]:
        mock = {
            "49.36.22.1": {"vpn_suspected": False, "proxy_score": 0.04, "tor_exit_node": False, "asn_name": "Jio Broadband"},
            "185.220.101.1": {"vpn_suspected": True, "proxy_score": 0.91, "tor_exit_node": True, "asn_name": "Anonymous Proxy Network"},
        }
        return mock.get(ip_address, {"vpn_suspected": False, "proxy_score": 0.1, "tor_exit_node": False, "asn_name": "Unknown"})

    def get_device_risk(self, device_id: str) -> Dict[str, Any]:
        if device_id == "DEV-44":
            return {"device_id": device_id, "mule_association_count": 4, "fraud_cluster_score": 0.86, "is_emulator_like": False}
        return {"device_id": device_id, "mule_association_count": 0, "fraud_cluster_score": 0.12, "is_emulator_like": False}


class InternalAPIHTTPConnectors(InternalAPIConnectors):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_case_annotations(self, customer_id: str) -> Dict[str, Any]:
        return http_get_json(f"{self.base_url}/case-annotations/{customer_id}")

    def get_ip_intelligence(self, ip_address: str) -> Dict[str, Any]:
        query = urlencode({"ip": ip_address})
        return http_get_json(f"{self.base_url}/ip-intelligence?{query}")

    def get_device_risk(self, device_id: str) -> Dict[str, Any]:
        return http_get_json(f"{self.base_url}/device-risk/{device_id}")


class HybridIPIntelConnector:
    def __init__(self, internal_connector: InternalAPIConnectors, external_base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.internal_connector = internal_connector
        self.external_base_url = external_base_url
        self.api_key = api_key

    def get_ip_intelligence(self, ip_address: str) -> Dict[str, Any]:
        internal = self.internal_connector.get_ip_intelligence(ip_address)
        if not self.external_base_url:
            return {**internal, "external_enrichment_used": False}

        try:
            query = urlencode({"ip": ip_address})
            headers = {"Accept": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            external = http_get_json(f"{self.external_base_url}?{query}", headers=headers)
            return {
                **internal,
                "external_enrichment_used": True,
                "external_geo": {
                    "country": external.get("country") or external.get("country_code"),
                    "city": external.get("city"),
                    "region": external.get("region"),
                    "org": external.get("org") or external.get("asn_name"),
                },
            }
        except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
            return {**internal, "external_enrichment_used": False}


class ResearcherAgent:
    def __init__(
        self,
        sql_tools: SQLTools,
        internal_connectors: InternalAPIConnectors,
        ip_connector: Optional[HybridIPIntelConnector] = None,
    ):
        self.sql = sql_tools
        self.internal = internal_connectors
        self.ip_connector = ip_connector or HybridIPIntelConnector(internal_connectors)

    def build_case(self, sentry_alert: Dict[str, Any]) -> Dict[str, Any]:
        metadata = sentry_alert["case_metadata"]
        customer_id = metadata["customer_id"]
        transaction_id = metadata["transaction_id"]

        customer = self.sql.fetch_one("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        transaction = self.sql.fetch_one("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
        if not customer or not transaction:
            raise ValueError("Missing customer or transaction in SQL demo store.")

        account_rows = self.sql.fetch_all("SELECT * FROM accounts WHERE customer_id = ?", (customer_id,))
        docs = self.sql.fetch_all("SELECT doc_type, doc_id, verified FROM onboarding_docs WHERE customer_id = ?", (customer_id,))
        logins = self.sql.fetch_all("SELECT * FROM logins WHERE customer_id = ? ORDER BY login_timestamp DESC", (customer_id,))
        device = self.sql.fetch_one("SELECT * FROM devices WHERE device_id = ?", (sentry_alert["trigger_context"]["device_id"],))
        linked_cases = self.sql.fetch_all("SELECT * FROM cases WHERE customer_id = ? ORDER BY created_at DESC", (customer_id,))
        entities = self.sql.fetch_all("SELECT * FROM entity_links WHERE customer_id = ? OR entity_value IN (?, ?, ?)", (customer_id, sentry_alert["trigger_context"]["shared_email"], sentry_alert["trigger_context"]["shared_phone"], sentry_alert["trigger_context"]["device_id"]))
        device_links = self.sql.fetch_all("SELECT DISTINCT customer_id FROM device_account_links WHERE device_id = ?", (sentry_alert["trigger_context"]["device_id"],))

        current_ip = sentry_alert["trigger_context"]["current_ip"]
        annotations = self.internal.get_case_annotations(customer_id)
        ip_intel = self.ip_connector.get_ip_intelligence(current_ip)
        device_risk = self.internal.get_device_risk(sentry_alert["trigger_context"]["device_id"])

        tx_behavior = self._summarize_transactions(customer_id)
        login_summary = self._summarize_logins(logins)
        prior_alert_count = len(linked_cases)
        evidence_score = self._score_evidence(sentry_alert, ip_intel, device_risk, prior_alert_count)

        return {
            "case_id": metadata["case_id"],
            "case_metadata": {**metadata, "trigger_source": sentry_alert["trigger_source"], "research_completed_at": utc_now()},
            "customer_profile": {
                "customer_name": customer["customer_name"],
                "age": customer["age"],
                "address": customer["address"],
                "country": customer["country"],
                "occupation": customer["occupation"],
                "business_type": customer["business_type"],
                "risk_level": customer["risk_level"],
                "kyc_status": customer["kyc_status"],
                "onboarding_date": customer["onboarding_date"],
                "account_age_days": self._days_between(customer["account_opened_date"]),
                "onboarding_docs": docs,
                "pep_match": bool(customer["pep_match"]),
                "sanctions_match": bool(customer["sanctions_match"]),
                "recent_profile_changes": annotations["recent_profile_changes"],
            },
            "account_history": {
                "accounts": account_rows,
                "linked_accounts": sorted({item["linked_account_id"] for item in entities if item["linked_account_id"] and item["customer_id"] != customer_id}),
                "transaction_behavior": tx_behavior,
                "beneficiary_patterns": {
                    "recent_beneficiaries": tx_behavior["recent_beneficiaries"],
                    "new_beneficiaries_7d": tx_behavior["new_beneficiaries_7d"],
                    "cross_border_transactions_30d": tx_behavior["cross_border_transactions_30d"],
                },
            },
            "ip_history": {
                "current_ip": current_ip,
                "ip_country": sentry_alert["trigger_context"]["current_ip_country"],
                "usual_countries": login_summary["usual_countries"],
                "recent_login_locations": login_summary["recent_login_locations"],
                "previous_ip_countries": login_summary["previous_ip_countries"],
                "first_seen_ip": login_summary["first_seen_ip"],
                "last_seen_ip": login_summary["last_seen_ip"],
                "vpn_suspected": ip_intel["vpn_suspected"],
                "proxy_score": ip_intel["proxy_score"],
                "tor_exit_node": ip_intel["tor_exit_node"],
                "asn_name": ip_intel["asn_name"],
                "external_enrichment_used": ip_intel.get("external_enrichment_used", False),
                "external_geo": ip_intel.get("external_geo"),
                "ip_country_mismatch": sentry_alert["trigger_context"]["current_ip_country"] != customer["country"],
                "impossible_travel_flag": self._is_impossible_travel(logins),
            },
            "device_fingerprint": {
                "device_id": device["device_id"] if device else sentry_alert["trigger_context"]["device_id"],
                "browser": device["browser"] if device else None,
                "os": device["os"] if device else None,
                "emulator_flag": bool(device["emulator_flag"]) if device else False,
                "rooted_or_jailbroken_flag": bool(device["rooted_flag"]) if device else False,
                "fingerprint_confidence": device["fingerprint_confidence"] if device else None,
                "first_seen_device": device["first_seen"] if device else None,
                "last_seen_device": device["last_seen"] if device else None,
                "shared_device_count": len(device_links),
                "linked_customer_ids": sorted(item["customer_id"] for item in device_links),
                "mule_association_count": device_risk["mule_association_count"],
                "fraud_cluster_score": device_risk["fraud_cluster_score"],
            },
            "entity_links": self._summarize_entities(entities),
            "historical_case_links": {
                "prior_alert_count": prior_alert_count,
                "prior_sar_count": sum(case["sar_filed"] for case in linked_cases),
                "prior_case_ids": [case["case_id"] for case in linked_cases],
                "closed_cases": sum(1 for case in linked_cases if case["status"] == "closed"),
                "analyst_notes": [case["analyst_note"] for case in linked_cases if case["analyst_note"]],
                "disposition_history": [{"case_id": case["case_id"], "disposition": case["disposition"], "status": case["status"], "created_at": case["created_at"]} for case in linked_cases],
            },
            "evidence_trace": self._build_evidence_trace(customer, transaction, current_ip, sentry_alert["trigger_context"]["device_id"], ip_intel, device_risk),
            "research_summary": self._build_summary(sentry_alert, logins, device_risk, ip_intel),
            "evidence_score": evidence_score,
            "decision_support": {
                "recommended_action": self._recommend_action(evidence_score),
                "reason_codes": self._reason_codes(sentry_alert, ip_intel, device_risk),
                "requires_manual_review": True,
                "missing_information": [],
            },
        }

    def _days_between(self, start_iso: str) -> int:
        return (datetime.utcnow() - parse_ts(start_iso).replace(tzinfo=None)).days

    def _summarize_transactions(self, customer_id: str) -> Dict[str, Any]:
        txns = self.sql.fetch_all("SELECT * FROM transactions WHERE customer_id = ? ORDER BY timestamp DESC", (customer_id,))
        amounts = [txn["amount"] for txn in txns]
        recent_beneficiaries = sorted({txn["beneficiary_name"] for txn in txns})
        return {
            "txn_count_30d": len(txns),
            "avg_txn_amount_30d": round(sum(amounts) / len(amounts), 2) if amounts else 0,
            "cross_border_transactions_30d": sum(1 for txn in txns if txn["destination_country"] != "IN"),
            "recent_beneficiaries": recent_beneficiaries,
            "new_beneficiaries_7d": min(len(recent_beneficiaries), 5),
        }

    def _summarize_logins(self, logins: List[Dict[str, Any]]) -> Dict[str, Any]:
        countries = [row["country"] for row in logins]
        return {
            "usual_countries": sorted(set(countries)),
            "recent_login_locations": [f'{row["city"]}, {row["country"]}' for row in logins[:5]],
            "previous_ip_countries": countries[1:5],
            "first_seen_ip": logins[-1]["ip_address"] if logins else None,
            "last_seen_ip": logins[0]["ip_address"] if logins else None,
        }

    def _is_impossible_travel(self, logins: List[Dict[str, Any]]) -> bool:
        if len(logins) < 2 or logins[0]["country"] == logins[1]["country"]:
            return False
        return (parse_ts(logins[0]["login_timestamp"]) - parse_ts(logins[1]["login_timestamp"])) <= timedelta(hours=4)

    def _summarize_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        grouped: Dict[str, Dict[str, Any]] = {}
        for entity in entities:
            bucket = grouped.setdefault(entity["entity_type"], {})
            item = bucket.setdefault(entity["entity_value"], {"value": entity["entity_value"], "linked_customers": set(), "linked_accounts": set()})
            item["linked_customers"].add(entity["customer_id"])
            if entity["linked_account_id"]:
                item["linked_accounts"].add(entity["linked_account_id"])
        return {
            key: [
                {
                    "value": item["value"],
                    "linked_customer_count": len(item["linked_customers"]),
                    "linked_customers": sorted(item["linked_customers"]),
                    "linked_accounts": sorted(item["linked_accounts"]),
                }
                for item in values.values()
            ]
            for key, values in grouped.items()
        }

    def _build_summary(self, sentry_alert: Dict[str, Any], logins: List[Dict[str, Any]], device_risk: Dict[str, Any], ip_intel: Dict[str, Any]) -> List[str]:
        items = []
        if self._is_impossible_travel(logins):
            items.append("Customer logged in from different countries within a short window, indicating impossible travel.")
        if ip_intel["vpn_suspected"]:
            items.append("Current login IP is associated with VPN or proxy behavior.")
        if device_risk["mule_association_count"]:
            items.append(f'Device has been linked to {device_risk["mule_association_count"]} accounts associated with prior mule-like behavior.')
        items.append(f'Alert was triggered by {sentry_alert["alert_summary"]["alert_type"]} with risk score {sentry_alert["alert_summary"]["risk_score"]}.')
        return items

    def _build_evidence_trace(self, customer: Dict[str, Any], transaction: Dict[str, Any], current_ip: str, device_id: str, ip_intel: Dict[str, Any], device_risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        retrieved_at = utc_now()
        return [
            {"finding": "Customer KYC profile retrieved", "source_system": "customer_master", "source_record_id": customer["customer_id"], "retrieved_at": retrieved_at, "confidence": 0.99},
            {"finding": "Flagged transaction context retrieved", "source_system": "transaction_ledger", "source_record_id": transaction["transaction_id"], "retrieved_at": retrieved_at, "confidence": 0.99},
            {"finding": f"IP intelligence lookup for {current_ip}", "source_system": "internal_ip_risk_api", "source_record_id": current_ip, "retrieved_at": retrieved_at, "confidence": 0.9 if ip_intel["proxy_score"] > 0.5 else 0.75},
            {"finding": f"Device graph lookup for {device_id}", "source_system": "internal_device_graph_api", "source_record_id": device_id, "retrieved_at": retrieved_at, "confidence": 0.88 if device_risk["fraud_cluster_score"] > 0.5 else 0.7},
        ]

    def _score_evidence(self, sentry_alert: Dict[str, Any], ip_intel: Dict[str, Any], device_risk: Dict[str, Any], prior_alert_count: int) -> float:
        score = sentry_alert["alert_summary"]["risk_score"] * 0.5
        score += ip_intel["proxy_score"] * 0.2
        score += min(device_risk["fraud_cluster_score"], 1.0) * 0.2
        score += min(prior_alert_count / 10.0, 0.1)
        return round(min(score, 0.99), 2)

    def _recommend_action(self, evidence_score: float) -> str:
        if evidence_score >= 0.85:
            return "escalate"
        if evidence_score >= 0.65:
            return "monitor"
        return "clear_with_note"

    def _reason_codes(self, sentry_alert: Dict[str, Any], ip_intel: Dict[str, Any], device_risk: Dict[str, Any]) -> List[str]:
        codes = [code["code"] for code in sentry_alert["alert_summary"]["reason_codes"]]
        if ip_intel["vpn_suspected"]:
            codes.append("VPN_OR_PROXY_SIGNAL")
        if device_risk["mule_association_count"] > 0:
            codes.append("SHARED_DEVICE_RISK")
        return sorted(set(codes))


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def ensure_internal_api_seed(path: Path) -> None:
    if path.exists():
        return
    seed = {
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
            "49.36.22.1": {
                "vpn_suspected": False,
                "proxy_score": 0.04,
                "tor_exit_node": False,
                "asn_name": "Jio Broadband"
            },
            "185.220.101.1": {
                "vpn_suspected": True,
                "proxy_score": 0.91,
                "tor_exit_node": True,
                "asn_name": "Anonymous Proxy Network"
            }
        },
        "device_risk": {
            "DEV-44": {
                "device_id": "DEV-44",
                "mule_association_count": 4,
                "fraud_cluster_score": 0.86,
                "is_emulator_like": False
            }
        }
    }
    write_json(path, seed)


def build_internal_connector(mode: str, internal_api_base_url: Optional[str]) -> InternalAPIConnectors:
    if mode == "http":
        if not internal_api_base_url:
            raise ValueError("--internal-api-base-url is required when --connector-mode=http")
        return InternalAPIHTTPConnectors(internal_api_base_url)
    return InternalAPIConnectors()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Researcher investigation dossier from a Sentry alert.")
    parser.add_argument("--alert", type=Path, default=DATA_DIR / "sample_sentry_alert.json")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "sample_researcher_output.json")
    parser.add_argument("--connector-mode", choices=["local", "http"], default="local")
    parser.add_argument("--internal-api-base-url", default=None)
    parser.add_argument("--external-ip-base-url", default=None)
    parser.add_argument("--external-ip-api-key", default=None)
    args = parser.parse_args()

    ensure_demo_db(DB_PATH)
    ensure_internal_api_seed(INTERNAL_API_DATA_PATH)
    sentry_alert = load_json(args.alert)
    internal_connector = build_internal_connector(args.connector_mode, args.internal_api_base_url)
    ip_connector = HybridIPIntelConnector(
        internal_connector,
        external_base_url=args.external_ip_base_url,
        api_key=args.external_ip_api_key,
    )
    result = ResearcherAgent(SQLTools(DB_PATH), internal_connector, ip_connector=ip_connector).build_case(sentry_alert)
    write_json(args.output, result)
    print(f"Researcher output written to {args.output}")


if __name__ == "__main__":
    main()
