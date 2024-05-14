import io
import ipaddress
import socket
from enum import Enum
from typing import Any, Tuple, cast
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from oauthlib.oauth2 import BackendApplicationClient
from playwright.sync_api import BrowserContext, Playwright, sync_playwright
from requests_oauthlib import OAuth2Session

from danswer.configs.app_configs import (
    INDEX_BATCH_SIZE,
    WEB_CONNECTOR_OAUTH_CLIENT_ID,
    WEB_CONNECTOR_OAUTH_CLIENT_SECRET,
    WEB_CONNECTOR_OAUTH_TOKEN_URL,
    WEB_CONNECTOR_VALIDATE_URLS,
)
from danswer.configs.constants import DocumentSource
from danswer.connectors.interfaces import GenerateDocumentsOutput, LoadConnector
from danswer.connectors.models import Document, Section
from danswer.file_processing.extract_file_text import pdf_to_text
from danswer.file_processing.html_utils import web_html_cleanup
from danswer.utils.logger import setup_logger

logger = setup_logger()


class WEB_CONNECTOR_VALID_SETTINGS(str, Enum):
    # Given a base site, index everything under that path
    RECURSIVE = "recursive"
    # Given a URL, index only the given page
    SINGLE = "single"
    # Given a sitemap.xml URL, parse all the pages in it
    SITEMAP = "sitemap"
    # Given a file upload where every line is a URL, parse all the URLs provided
    UPLOAD = "upload"


def protected_url_check(url: str) -> None:
    """Couple considerations:
    - DNS mapping changes over time so we don't want to cache the results
    - Fetching this is assumed to be relatively fast compared to other bottlenecks like reading
      the page or embedding the contents
    - To be extra safe, all IPs associated with the URL must be global
    - This is to prevent misuse and not explicit attacks
    """
    if not WEB_CONNECTOR_VALIDATE_URLS:
        return

    parse = urlparse(url)
    if parse.scheme != "http" and parse.scheme != "https":
        raise ValueError("URL must be of scheme https?://")

    if not parse.hostname:
        raise ValueError("URL must include a hostname")

    try:
        # This may give a large list of IP addresses for domains with extensive DNS configurations
        # such as large distributed systems of CDNs
        info = socket.getaddrinfo(parse.hostname, None)
    except socket.gaierror as e:
        raise ConnectionError(f"DNS resolution failed for {parse.hostname}: {e}")

    for address in info:
        ip = address[4][0]
        if not ipaddress.ip_address(ip).is_global:
            raise ValueError(
                f"Non-global IP address detected: {ip}, skipping page {url}. "
                f"The Web Connector is not allowed to read loopback, link-local, or private ranges"
            )


def check_internet_connection(url: str) -> None:
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
    except (requests.RequestException, ValueError):
        raise Exception(f"Unable to reach {url} - check your internet connection")


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_internal_links(
        current_url: str, soup: BeautifulSoup, should_ignore_pound: bool = True
) -> set[str]:
    internal_links = set()
    for link in soup.find_all("a"):
        href = link.get("href")
        if not href:
            continue

        if should_ignore_pound and "#" in href:
            href = href.split("#")[0]

        if not is_valid_url(href):
            # Relative path handling
            href = urljoin(current_url, href)

        if urlparse(href).netloc == urlparse(current_url).netloc:
            internal_links.add(href)
    iframe = soup.find("iframe")
    if iframe:
        iframe_src = iframe.get("src")
        if iframe_src and is_valid_url(iframe_src):
            internal_links.add(iframe_src)

    return internal_links


def start_playwright() -> Tuple[Playwright, BrowserContext]:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context()

    if (
        WEB_CONNECTOR_OAUTH_CLIENT_ID
        and WEB_CONNECTOR_OAUTH_CLIENT_SECRET
        and WEB_CONNECTOR_OAUTH_TOKEN_URL
    ):
        client = BackendApplicationClient(client_id=WEB_CONNECTOR_OAUTH_CLIENT_ID)
        oauth = OAuth2Session(client=client)
        token = oauth.fetch_token(
            token_url=WEB_CONNECTOR_OAUTH_TOKEN_URL,
            client_id=WEB_CONNECTOR_OAUTH_CLIENT_ID,
            client_secret=WEB_CONNECTOR_OAUTH_CLIENT_SECRET,
        )
        context.set_extra_http_headers(
            {"Authorization": "Bearer {}".format(token["access_token"])}
        )

    return playwright, context


def extract_urls_from_sitemap(sitemap_url: str) -> list[str]:
    response = requests.get(sitemap_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    return [
        _ensure_absolute_url(sitemap_url, loc_tag.text)
        for loc_tag in soup.find_all("loc")
    ]


def _ensure_absolute_url(source_url: str, maybe_relative_url: str) -> str:
    if not urlparse(maybe_relative_url).netloc:
        return urljoin(source_url, maybe_relative_url)
    return maybe_relative_url


def _ensure_valid_url(url: str) -> str:
    if "://" not in url:
        return "https://" + url
    return url


def _read_urls_file(location: str) -> list[str]:
    with open(location, "r") as f:
        urls = [_ensure_valid_url(line.strip()) for line in f if line.strip()]
    return urls


class AdcubumConnector(LoadConnector):
    def __init__(
        self,
        base_url: str,  # Can't change this without disrupting existing users
        web_connector_type: str = WEB_CONNECTOR_VALID_SETTINGS.RECURSIVE.value,
        mintlify_cleanup: bool = True,  # Mostly ok to apply to other websites as well
        batch_size: int = INDEX_BATCH_SIZE,
    ) -> None:
        self.mintlify_cleanup = mintlify_cleanup
        self.batch_size = batch_size
        self.recursive = False

        if web_connector_type == WEB_CONNECTOR_VALID_SETTINGS.RECURSIVE.value:
            self.recursive = True
            self.to_visit_list = [_ensure_valid_url(base_url)]
            return

        elif web_connector_type == WEB_CONNECTOR_VALID_SETTINGS.SINGLE.value:
            self.to_visit_list = [_ensure_valid_url(base_url)]

        elif web_connector_type == WEB_CONNECTOR_VALID_SETTINGS.SITEMAP:
            self.to_visit_list = extract_urls_from_sitemap(_ensure_valid_url(base_url))

        elif web_connector_type == WEB_CONNECTOR_VALID_SETTINGS.UPLOAD:
            logger.warning(
                "This is not a UI supported Web Connector flow, "
                "are you sure you want to do this?"
            )
            self.to_visit_list = _read_urls_file(base_url)

        else:
            raise ValueError(
                "Invalid Web Connector Config, must choose a valid type between: " ""
            )

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        if credentials:
            logger.warning("Unexpected credentials provided for Web Connector")
        return None

    def load_from_state(self) -> GenerateDocumentsOutput:
        """Traverses through all pages found on the website
        and converts them into documents"""
        visited_links: set[str] = set()
        to_visit: list[str] = self.to_visit_list
        base_url = to_visit[0]  # For the recursive case
        doc_batch: list[Document] = []

        # Needed to report error
        at_least_one_doc = False
        last_error = None

        playwright, context = start_playwright()
        restart_playwright = False
        while to_visit:
            current_url = to_visit.pop()
            if current_url in visited_links:
                continue
            visited_links.add(current_url)

            try:
                protected_url_check(current_url)
            except Exception as e:
                last_error = f"Invalid URL {current_url} due to {e}"
                logger.warning(last_error)
                continue

            logger.info(f"Visiting {current_url}")

            try:
                check_internet_connection(current_url)
                if restart_playwright:
                    playwright, context = start_playwright()
                    restart_playwright = False

                if current_url.split(".")[-1] == "pdf":
                    # PDF files are not checked for links
                    response = requests.get(current_url)
                    page_text = pdf_to_text(file=io.BytesIO(response.content))

                    doc_batch.append(
                        Document(
                            id=current_url,
                            sections=[Section(link=current_url, text=page_text)],
                            source=DocumentSource.ADCUBUM,
                            semantic_identifier=current_url.split(".")[-1],
                            metadata={},
                        )
                    )
                    continue

                page = context.new_page()
                page_response = page.goto(current_url, wait_until="networkidle")
                # wait for page redirects to finish
                page.wait_for_load_state('networkidle')
                final_page = page.url
                if final_page != current_url:
                    logger.info(f"Redirected to {final_page}")
                    protected_url_check(final_page)
                    current_url = final_page
                    if current_url in visited_links:
                        logger.info("Redirected page already indexed")
                        continue
                    visited_links.add(current_url)

                content = page.content()
                soup = BeautifulSoup(content, "html.parser")

                if self.recursive:
                    if "#" not in current_url and urlparse(base_url).netloc == urlparse(current_url).netloc:
                        internal_links = get_internal_links(current_url, soup)
                        for link in internal_links:
                            if link not in visited_links and link not in to_visit:
                                to_visit.append(link)

                if page_response and str(page_response.status)[0] in ("4", "5"):
                    last_error = f"Skipped indexing {current_url} due to HTTP {page_response.status} response"
                    logger.info(last_error)
                    continue

                parsed_html = web_html_cleanup(soup, self.mintlify_cleanup, page=page,
                                               additional_element_types_to_discard=["nav", "section", "footer", "header"])

                doc_batch.append(
                    Document(
                        id=current_url,
                        sections=[
                            Section(link=current_url, text=parsed_html.cleaned_text)
                        ],
                        source=DocumentSource.ADCUBUM,
                        semantic_identifier=parsed_html.title or current_url,
                        metadata={},
                    )
                )

                page.close()
            except Exception as e:
                last_error = f"Failed to fetch '{current_url}': {e}"
                logger.error(last_error)
                playwright.stop()
                restart_playwright = True
                continue

            if len(doc_batch) >= self.batch_size:
                playwright.stop()
                restart_playwright = True
                at_least_one_doc = True
                yield doc_batch
                doc_batch = []

        if doc_batch:
            playwright.stop()
            at_least_one_doc = True
            yield doc_batch

        if not at_least_one_doc:
            if last_error:
                raise RuntimeError(last_error)
            raise RuntimeError("No valid pages found.")


if __name__ == "__main__":
    # connector = AdcubumConnector(
    #     base_url="https://main-adcubum-syrius-documentation.apps.corp.clusters.adcubum.com/en-GB/index.html",
    #     web_connector_type = WEB_CONNECTOR_VALID_SETTINGS.RECURSIVE.value
    # )
    # connector = AdcubumConnector(
    #     base_url="https://devdocs.apps.corp.clusters.adcubum.com/ui/syrius3/3.14/index.html",
    #     web_connector_type=WEB_CONNECTOR_VALID_SETTINGS.RECURSIVE.value
    # )

    connector = AdcubumConnector(
        base_url="https://devdocs.apps.corp.clusters.adcubum.com/ui/syrius3/3.25/index.html",
        web_connector_type=WEB_CONNECTOR_VALID_SETTINGS.RECURSIVE.value
    )

    document_batches = connector.load_from_state()
    print(next(document_batches))
