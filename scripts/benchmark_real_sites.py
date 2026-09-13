"""Bounded end-to-end benchmark against public sites; read-only and no browser rendering."""
from __future__ import annotations
import json, sys, time
from skills.audit_orchestrator import audit_site_report
from skills.crawl_render_audit.scripts.crawler import WebsiteCrawler

SITES = ["https://www.adobe.com", "https://www.python.org", "https://www.wikipedia.org", "https://www.nasa.gov"]

def run(url):
    crawler=WebsiteCrawler(max_pages=5,max_depth=1,max_requests=30,max_seconds=45,max_rendered_pages=0)
    start=time.perf_counter()
    report=audit_site_report(url,crawler=crawler)
    elapsed=round(time.perf_counter()-start,2)
    return {"site":url,"seconds":elapsed,"pages":report.get("coverage",{}).get("pages_audited",0),"findings":report["summary"]["total_findings"],"score":report.get("readiness_score",{}).get("overall"),"journey":report.get("referral_journey",{}).get("overall"),"request_stats":report.get("coverage",{}).get("crawl_stats",{})}

if __name__ == "__main__":
    results=[]
    for site in sys.argv[1:] or SITES:
        try: results.append(run(site))
        except Exception as exc: results.append({"site":site,"error":f"{type(exc).__name__}: {exc}"})
    print(json.dumps(results,indent=2))
