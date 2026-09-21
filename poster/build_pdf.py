#!/usr/bin/env python3
"""
Baut das A0-Poster-PDF aus dem HTML.

    pip install playwright
    playwright install chromium

    python build_pdf.py                                   -> poster-a0.pdf
    python build_pdf.py "Research Poster A0.dc.html" out.pdf

Serviert den Projektordner per lokalem HTTP-Server (file:// blockiert das
Laden von support.js / doc-page.js), rendert die Seite und druckt exakt A0.
"""
import functools
import http.server
import socketserver
import sys
import threading
import urllib.parse
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
SRC = sys.argv[1] if len(sys.argv) > 1 else "Research Poster A0.dc.html"
OUT = sys.argv[2] if len(sys.argv) > 2 else "poster-a0.pdf"

WIDTH_MM, HEIGHT_MM = 841, 1189  # A0 hoch


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve() -> tuple[socketserver.TCPServer, int]:
    handler = functools.partial(Handler, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def main() -> None:
    if not (ROOT / SRC).exists():
        sys.exit(f"nicht gefunden: {SRC}")

    httpd, port = serve()
    url = f"http://127.0.0.1:{port}/{urllib.parse.quote(SRC)}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--font-render-hinting=none"])
            # px bei 96 dpi, damit CSS-mm im Layout dem Druckbogen entsprechen
            page = browser.new_page(viewport={
                "width": round(WIDTH_MM / 25.4 * 96),
                "height": round(HEIGHT_MM / 25.4 * 96),
            })
            page.on("console", lambda m: m.type == "error" and print("[page]", m.text))

            page.goto(url, wait_until="networkidle", timeout=120_000)
            try:
                page.wait_for_function(
                    "() => !!document.querySelector('doc-page')"
                    " && document.fonts.status === 'loaded'",
                    timeout=60_000,
                )
            except Exception:
                print("Warnung: doc-page/Fonts nicht bereit, drucke trotzdem")
            page.wait_for_timeout(1500)

            page.pdf(
                path=str(ROOT / OUT),
                width=f"{WIDTH_MM}mm",
                height=f"{HEIGHT_MM}mm",
                print_background=True,
                prefer_css_page_size=False,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
    finally:
        httpd.shutdown()

    print(f"geschrieben: {OUT}  ({WIDTH_MM}\u00d7{HEIGHT_MM} mm, A0 hoch)")


if __name__ == "__main__":
    main()
