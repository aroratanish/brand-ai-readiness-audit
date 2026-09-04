from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


@dataclass
class RenderResult:
    url: str
    final_url: Optional[str] = None
    rendered_html: str = ""
    title: Optional[str] = None
    status_code: Optional[int] = None
    error: Optional[str] = None


class Renderer:
    def __init__(
        self,
        timeout_ms: int = 30000,
        wait_after_load_ms: int = 2000,
    ):
        self.timeout_ms = timeout_ms
        self.wait_after_load_ms = wait_after_load_ms

    def render(self, url: str) -> RenderResult:
        result = RenderResult(url=url)

        with sync_playwright() as p:
            browser = None

            try:
                browser = p.chromium.launch(headless=True)

                page = browser.new_page(
                    java_script_enabled=True,
                    viewport={
                        "width": 1440,
                        "height": 900,
                    },
                )

                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )

                result.final_url = page.url

                if response is not None:
                    result.status_code = response.status

                page.wait_for_timeout(self.wait_after_load_ms)

                result.rendered_html = page.content()
                result.title = page.title()

            except PlaywrightTimeoutError:
                result.error = "Rendering timed out."

                try:
                    result.final_url = page.url
                    result.rendered_html = page.content()
                    result.title = page.title()
                except Exception:
                    pass

            except Exception as exc:
                result.error = f"{type(exc).__name__}: {exc}"

                try:
                    result.final_url = page.url
                    result.rendered_html = page.content()
                    result.title = page.title()
                except Exception:
                    pass

            finally:
                if browser is not None:
                    browser.close()

        return result