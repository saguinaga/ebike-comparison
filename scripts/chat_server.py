"""Optional local chat proxy for Grok / SpaceXAI (keeps XAI_API_KEY server-side).

Usage:
  set XAI_API_KEY=your-key
  python scripts/chat_server.py

Then set chatApiUrl in app-config at build time, or patch docs/index.html:
  "chatApiUrl": "http://127.0.0.1:8787/chat"
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "bikes.json"
XAI_URL = "https://api.x.ai/v1/responses"
MODEL = os.environ.get("XAI_CHAT_MODEL", "grok-4.5")


def load_catalog_snippet(product_id: str | None, limit: int = 8) -> str:
    bikes = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    lines = []
    if product_id:
        match = next((b for b in bikes if b.get("id") == product_id), None)
        if match:
            lines.append(f"Current product: {match.get('brand')} {match.get('model')} (id={product_id})")
    for b in bikes:
        if b.get("is_baseline"):
            continue
        lines.append(
            f"- {b.get('brand')} {b.get('model')}: ${b.get('landed_price_usd') or b.get('price_usd')}, "
            f"{b.get('max_speed_mph')} mph, safety {b.get('safety_score')}, type {b.get('vehicle_type', 'ebike')}"
        )
        if len(lines) >= limit + 1:
            break
    return "\n".join(lines)


class ChatHandler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/chat":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        message = (body.get("message") or "").strip()
        product_id = body.get("productId")
        api_key = os.environ.get("XAI_API_KEY")
        if not api_key:
            self.send_response(503)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "XAI_API_KEY not set"}).encode())
            return

        catalog = load_catalog_snippet(product_id)
        system = (
            "You are a helpful advisor for a family comparing e-bikes and e-scooters in Huntington Beach, CA. "
            "Use only the catalog facts below. Be concise. Mention helmet rules, Class 3 under-16 ban, and 10 mph path limits when relevant. "
            "Not legal or medical advice.\n\nCatalog:\n" + catalog
        )
        payload = {
            "model": MODEL,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
        }
        req = Request(
            XAI_URL,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
        except Exception as exc:
            self.send_response(502)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode())
            return

        reply = data.get("output_text") or data.get("choices", [{}])[0].get("message", {}).get("content", "")
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"reply": reply}).encode())

    def log_message(self, format, *args):
        return


def main():
    port = int(os.environ.get("CHAT_PORT", "8787"))
    server = HTTPServer(("127.0.0.1", port), ChatHandler)
    print(f"Chat proxy on http://127.0.0.1:{port}/chat (model {MODEL})")
    server.serve_forever()


if __name__ == "__main__":
    main()