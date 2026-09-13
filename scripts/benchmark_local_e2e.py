"""Deterministic local end-to-end smoke benchmark for environments without outbound HTTP."""
from __future__ import annotations
import json, threading, time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from skills.audit_orchestrator import audit_site_report
from skills.crawl_render_audit.scripts.crawler import WebsiteCrawler

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

root=Path(__file__).resolve().parents[1]/"tests"/"fixtures"/"commerce"
server=ThreadingHTTPServer(("127.0.0.1",0), lambda *a,**k: Quiet(*a,directory=str(root),**k))
thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
try:
    url=f"http://127.0.0.1:{server.server_port}/"
    crawler=WebsiteCrawler(max_pages=5,max_depth=1,max_requests=30,max_seconds=45,max_rendered_pages=0)
    start=time.perf_counter(); report=audit_site_report(url,crawler=crawler); elapsed=time.perf_counter()-start
    print(json.dumps({"site":url,"seconds":round(elapsed,3),"pages":report["coverage"]["pages_audited"],"findings":report["summary"]["total_findings"],"score":report["readiness_score"]["overall"]},indent=2))
finally:
    server.shutdown(); server.server_close()
