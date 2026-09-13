"""Competitive/polish layer: evidence graph, referral journey, action ranking, and safe corroboration."""
from __future__ import annotations
import re, time, ipaddress
from collections import defaultdict
from difflib import SequenceMatcher
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from skills.crawl_render_audit.scripts.models import PageResult

SOCIAL_HOSTS = {"facebook.com","www.facebook.com","instagram.com","www.instagram.com","linkedin.com","www.linkedin.com","x.com","twitter.com","youtube.com","www.youtube.com","tiktok.com","www.tiktok.com"}
TRACKER_HOSTS = {"google-analytics.com","googletagmanager.com","doubleclick.net","facebook.net","connect.facebook.net"}

def _text(page):
    soup=BeautifulSoup(page.raw_html or "", "lxml")
    for e in soup(["script","style","noscript","template","svg"]): e.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())

def _types(obj):
    t=obj.get("@type") if isinstance(obj,dict) else None
    vals=t if isinstance(t,list) else [t]
    return {str(x).lower() for x in vals if x}

def iter_jsonld(value):
    if isinstance(value,list):
        for x in value: yield from iter_jsonld(x)
    elif isinstance(value,dict):
        yield value
        if "@graph" in value: yield from iter_jsonld(value["@graph"])

def organization_name(pages):
    for p in pages:
        for o in iter_jsonld(p.json_ld):
            if _types(o) & {"organization","corporation","brand"} and isinstance(o.get("name"),str):
                return o["name"].strip()
    for p in pages:
        text=_text(p)
        if p.depth==0 and p.title: return p.title.split("|")[0].strip()
    return ""

def build_evidence_graph(pages):
    """Build a compact, explainable graph of pages, entities, commercial facts and links."""
    nodes=[]; edges=[]; seen=set(); prices_by_product=defaultdict(list)
    def node(i, kind, label, url=None, evidence=None):
        if i in seen: return
        seen.add(i)
        item={"id":i,"kind":kind,"label":label}
        if url: item["url"]=url
        if evidence: item["evidence"]=evidence
        nodes.append(item)
    for p in pages:
        u=p.final_url or p.url; pid="page:"+u; node(pid,"page",u,u)
        for o in iter_jsonld(p.json_ld):
            name=o.get("name"); types=_types(o)
            if name and types:
                kind=sorted(types)[0]
                oid=f"{kind}:{str(name).lower()}"
                node(oid,kind,str(name)); edges.append({"from":pid,"to":oid,"relation":"declares"})
                offers=o.get("offers") if isinstance(o.get("offers"),list) else [o.get("offers")]
                for offer in offers:
                    if isinstance(offer,dict) and offer.get("price") is not None:
                        currency=str(offer.get("priceCurrency","")).upper()
                        price=f"price:{str(name).lower()}:{offer.get('price')}:{currency}"
                        node(price,"price",f"{offer.get('price')} {currency}" ,evidence={"source":u,"structured":True})
                        edges.append({"from":oid,"to":price,"relation":"has_price","source":u})
                        prices_by_product[str(name).lower()].append((price,u))
        # Add a visible-price fact when a currency-like price is plainly present.
        text=_text(p)
        for m in re.finditer(r"(?:[$€£₹]|USD|EUR|GBP|INR)\s?\d[\d,.]*|\d[\d,.]*\s?(?:USD|EUR|GBP|INR)", text, re.I):
            label=m.group(0)[:40]
            vid=f"visible-price:{u}:{re.sub(r'\W+','',label.lower())}"
            node(vid,"visible_price",label,evidence={"source":u,"structured":False})
            edges.append({"from":pid,"to":vid,"relation":"shows_visible_fact"})
            break
        for link in (p.internal_links or [])[:50]:
            edges.append({"from":pid,"to":"page:"+link,"relation":"links_to"})
    for product, entries in prices_by_product.items():
        unique={x[0] for x in entries}
        if len(unique)>1:
            for i,a in enumerate(entries):
                for b in entries[i+1:]:
                    if a[0]!=b[0]: edges.append({"from":a[0],"to":b[0],"relation":"conflicts_with","product":product,"sources":[a[1],b[1]]})
    return {"nodes":nodes,"edges":edges,"node_count":len(nodes),"edge_count":len(edges),"conflict_edges":sum(1 for e in edges if e.get("relation")=="conflicts_with")}

def build_referral_journey(pages):
    """Estimate whether an AI-referred visitor can move from discovery to conversion."""
    if not pages: return {"overall":0,"stages":{},"bottleneck":None,"stage_evidence":{}}
    decision_pages=[p for p in pages if p.depth==0 or re.search(r"/(product|pricing|service|solution|plan)s?(/|$)", (p.final_url or p.url), re.I)]
    def has_action(p): return bool(re.search(r"\b(buy|book|demo|trial|quote|contact|subscribe|get started|apply|download|request)\b", _text(p), re.I)) or bool(re.search(r"<form\b|mailto:|tel:",p.raw_html or "",re.I))
    def has_identity(p): return bool(p.h1) and len(_text(p).split())>=10
    def has_decision_facts(p):
        t=_text(p).lower()
        return bool(re.search(r"\b(price|pricing|cost|feature|benefit|specification|availability|included|plan)\b",t))
    stage_evidence={
        "discovery": {"covered_pages":len(pages),"pages_with_title_and_h1":sum(bool((p.title or '').strip()) and bool(p.h1) for p in pages)},
        "understanding": {"pages_with_identity_context":sum(has_identity(p) for p in pages)},
        "trust": {"pages_with_structured_or_canonical_evidence":sum(bool(p.json_ld) or bool(p.canonical) for p in pages)},
        "decision": {"decision_pages":len(decision_pages),"pages_with_decision_facts":sum(has_decision_facts(p) for p in decision_pages),"pages_with_action":sum(has_action(p) for p in decision_pages)},
        "conversion": {"pages_with_action_path":sum(has_action(p) for p in pages)},
    }
    stages={
        "discovery": round(100*stage_evidence["discovery"]["pages_with_title_and_h1"]/len(pages),1),
        "understanding": round(100*stage_evidence["understanding"]["pages_with_identity_context"]/len(pages),1),
        "trust": round(100*stage_evidence["trust"]["pages_with_structured_or_canonical_evidence"]/len(pages),1),
        "decision": round(100*stage_evidence["decision"]["pages_with_action"] / max(1,len(decision_pages)),1),
        "conversion": round(100*stage_evidence["conversion"]["pages_with_action_path"]/len(pages),1),
    }
    bottleneck=min(stages,key=stages.get)
    return {"overall":round(sum(stages.values())/len(stages),1),"stages":stages,"bottleneck":bottleneck,"stage_evidence":stage_evidence,"interpretation":f"The lowest-scoring stage is {bottleneck}; improve that stage first before adding lower-impact polish."}

def rank_actions(findings):
    ranked=[]
    sev_weight={"critical":100,"high":80,"medium":55,"low":30}
    effort_terms={"add":35,"rewrite":20,"synchronize":55,"repair":25,"investigate":65,"server-render":70,"implement":60,"review":15,"remove":20,"provide":30}
    for f in findings:
        action=str(f.get("suggested_action",{}).get("summary", ""))
        impact=sev_weight.get(f.get("severity","low"),30)
        if f.get("confidence")=="low": impact-=10
        if f.get("category") in {"discoverability","freshness","entity-trust"}: impact+=5
        impact=max(10,min(100,impact))
        effort=40
        for term,val in effort_terms.items():
            if term in action.lower(): effort=max(10,min(95,effort+val-40))
        score=round(impact*0.7+(100-effort)*0.3,1)
        item=dict(f); item["impact_score"]=impact; item["effort_score"]=effort; item["priority_score"]=score
        ranked.append(item)
    ranked.sort(key=lambda x:(-x["priority_score"],-x["impact_score"],x.get("id","")))
    for i,x in enumerate(ranked,1): x["priority_rank"]=i
    return ranked

def _safe_public_url(url):
    parsed=urlparse(url)
    if parsed.scheme not in {"http","https"} or not parsed.hostname: return False
    host=parsed.hostname.lower().removeprefix("www.")
    if host in {"localhost","127.0.0.1","0.0.0.0","::1"} or host.endswith(".local"): return False
    try:
        if ipaddress.ip_address(host).is_private: return False
    except ValueError:
        pass
    return True

def external_corroboration(pages, max_sources=3, timeout=5):
    """Bounded, read-only corroboration from already-linked public external HTML pages."""
    org=organization_name(pages); candidates=[]; seen=set()
    if not org: return {"status":"not_available","reason":"No organization identity was extracted."}
    first_party={ (urlparse(p.final_url or p.url).hostname or '').lower().removeprefix('www.') for p in pages }
    for p in pages:
        for u in p.external_links or []:
            host=(urlparse(u).hostname or '').lower().removeprefix('www.')
            if not _safe_public_url(u) or not host or host in SOCIAL_HOSTS or host in TRACKER_HOSTS or host in first_party: continue
            key=u.split('#')[0]
            if key in seen: continue
            seen.add(key); candidates.append(key)
            if len(candidates)>=max_sources: break
        if len(candidates)>=max_sources: break
    results=[]
    for u in candidates:
        try:
            parsed=urlparse(u); rp=RobotFileParser(); rp.set_url(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
            try: rp.read()
            except Exception: pass
            if not rp.can_fetch("BrandAIReadinessAudit/1.0",u):
                results.append({"url":u,"status":"robots_blocked"}); continue
            r=requests.get(u,timeout=timeout,allow_redirects=True,headers={"User-Agent":"BrandAIReadinessAudit/1.0 (read-only corroboration)"})
            if "text/html" not in r.headers.get("content-type","").lower(): continue
            soup=BeautifulSoup(r.text,"lxml")
            title=" ".join((soup.title.get_text(" ",strip=True) if soup.title else "").split())
            desc=soup.find("meta",attrs={"name":re.compile("description",re.I)})
            description=desc.get("content","") if desc else ""
            combined=f"{title} {description}".lower(); org_norm=re.sub(r"[^a-z0-9]+"," ",org.lower()).strip(); combined_norm=re.sub(r"[^a-z0-9]+"," ",combined).strip()
            tokens=[t for t in org_norm.split() if len(t)>2]
            token_hits=sum(t in combined_norm for t in tokens)
            ratio=SequenceMatcher(None,org_norm,combined_norm).ratio()
            matched=bool(tokens) and token_hits>=max(1,(len(tokens)+1)//2) or ratio>=.60
            results.append({"url":r.url,"status_code":r.status_code,"title":title,"organization_match":matched,"match_score":round(max(ratio, token_hits/max(1,len(tokens))),2)})
        except requests.RequestException as exc:
            results.append({"url":u,"error":str(exc)})
    corroborated=[x for x in results if x.get("organization_match")]
    return {"status":"checked","organization":org,"sources_checked":len(results),"corroborated_sources":corroborated,"independent_source_count":len(corroborated),"method":"Only already-linked public external HTML pages are checked; social/tracker domains, private hosts, and robots-blocked pages are excluded. Lack of corroboration is not treated as a defect."}

