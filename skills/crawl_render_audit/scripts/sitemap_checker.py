import requests
import xml.etree.ElementTree as ET

from urllib.parse import urljoin


USER_AGENT = "BrandAIReadinessAudit/1.0"


def get_sitemap_url(site_url: str) -> str:

    return urljoin(
        site_url,
        "/sitemap.xml"
    )


def fetch_sitemap(
    sitemap_url: str
):

    try:

        response = requests.get(
            sitemap_url,
            timeout=10,
            headers={
                "User-Agent": USER_AGENT
            }
        )

        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "content": response.text,
            "error": None
        }

    except requests.RequestException as exc:

        return {
            "success": False,
            "status_code": None,
            "content": "",
            "error": str(exc)
        }


def parse_sitemap(
    sitemap_url: str
):

    data = fetch_sitemap(
        sitemap_url
    )

    result = {
        "url": sitemap_url,
        "exists": data["success"],
        "status_code": data["status_code"],
        "type": None,
        "urls": [],
        "sitemaps": [],
        "error": data["error"]
    }

    if not data["success"]:
        return result

    try:

        root = ET.fromstring(
            data["content"]
        )

        root_tag = root.tag.lower()

        if root_tag.endswith("urlset"):

            result["type"] = "urlset"

            for url_element in root:

                for child in url_element:

                    if child.tag.lower().endswith("loc"):

                        if child.text:

                            result["urls"].append(
                                child.text.strip()
                            )

        elif root_tag.endswith("sitemapindex"):

            result["type"] = "sitemapindex"

            for sitemap_element in root:

                for child in sitemap_element:

                    if child.tag.lower().endswith("loc"):

                        if child.text:

                            result["sitemaps"].append(
                                child.text.strip()
                            )

        return result

    except ET.ParseError as exc:

        result["error"] = (
            f"Invalid XML: {exc}"
        )

        return result