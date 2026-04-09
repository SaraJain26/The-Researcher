import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "sample_data" / "internal_api_data.json"


def load_seed_data(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class InternalAPIHandler(BaseHTTPRequestHandler):
    seed_data = {}

    def _send_json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.strip("/").split("/")

        if parsed.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if len(path) == 2 and path[0] == "case-annotations":
            customer_id = path[1]
            payload = self.seed_data["case_annotations"].get(customer_id)
            self._send_json(200 if payload else 404, payload or {"error": "not found"})
            return

        if parsed.path == "/ip-intelligence":
            params = parse_qs(parsed.query)
            ip = params.get("ip", [None])[0]
            payload = self.seed_data["ip_intelligence"].get(ip)
            self._send_json(200 if payload else 404, payload or {"error": "not found"})
            return

        if len(path) == 2 and path[0] == "device-risk":
            device_id = path[1]
            payload = self.seed_data["device_risk"].get(device_id)
            self._send_json(200 if payload else 404, payload or {"error": "not found"})
            return

        self._send_json(404, {"error": "unknown route"})

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run mock internal APIs for The Researcher.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--seed", type=Path, default=DATA_PATH)
    args = parser.parse_args()

    InternalAPIHandler.seed_data = load_seed_data(args.seed)
    server = ThreadingHTTPServer((args.host, args.port), InternalAPIHandler)
    print(f"Mock internal API server running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
