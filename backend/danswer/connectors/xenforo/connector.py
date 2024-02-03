"""
This is the XenforoConnector class. It is used to connect to a Xenforo forum and load or update documents from the forum.

To use this class, you need to provide the URL of the Xenforo forum board you want to connect to when creating an instance
of the class. The URL should be a string that starts with 'http://' or 'https://', followed by the domain name of the 
forum, followed by the board name. For example:

    base_url = 'https://www.example.com/forum/boards/some-topic/'

The `load_from_state` method is used to load documents from the forum. It takes an optional `state` parameter, which 
can be used to specify a state from which to start loading documents.
"""
import re
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import pytz
import requests
from bs4 import BeautifulSoup
from danswer.configs.constants import DocumentSource
from danswer.connectors.interfaces import (
    LoadConnector,
    GenerateDocumentsOutput,
)
from danswer.connectors.models import Document
from danswer.connectors.models import Section
from danswer.utils.logger import setup_logger


logger = setup_logger()


def requestsite(self, url):
    try:
        response = requests.get(
            url, cookies=self.cookies, headers=self.headers, timeout=10
        )
        if response.status_code != 200:
            logger.error(
                f"<{url}> Request Error: {response.status_code} - {response.reason}"
            )
        return BeautifulSoup(response.text, "html.parser")
    except TimeoutError:
        logger.error("Timed out Error.")
        pass
    except Exception as e:
        logger.error(f"Error on {url}")
        logger.exception(e)
        pass
    return BeautifulSoup("", "html.parser")


def get_title(soup):
    title = soup.find("h1", "p-title-value").text
    for char in (";", ":", "!", "*", "/", "\\", "?", '"', "<", ">", "|"):
        title = title.replace(char, "_")
    return title


def get_pages(soup, url):
    page_tags = soup.select("li.pageNav-page")
    page_numbers = []
    for button in page_tags:
        if re.match("^\d+$", button.text):
            page_numbers.append(button.text)

    try:
        max_pages = max(page_numbers, key=int)
    except ValueError:
        max_pages = 1

    all_pages = []
    for x in range(1, int(max_pages) + 1):
        all_pages.append(f"{url}page-{x}")
    return all_pages


def parse_post_date(post_element: BeautifulSoup):
    date_string = post_element.find('time')['datetime']
    post_date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
    return post_date


def scrape_page_posts(soup, url, last_run_date) -> list:
    title = get_title(soup)
    documents = []
    for post in soup.find_all("div", class_="message-main"):
        post_date = parse_post_date(post)
        if XenforoConnector.initial_run or post_date > last_run_date:
            # Process all posts if it's the initial run, otherwise only newer than the last run date
            post_text = post.get_text() + "\n"
            document = Document(
                id=f"{DocumentSource.XENFORO.value}:{title}",
                sections=[Section(link=url, text=post_text)],
                title=title,
                text=post_text,
                source=DocumentSource.WEB,
                semantic_identifier=title,
                metadata={"type": "post"},
            )
            documents.append(document)
    return documents


def get_threads(self, url):
    soup = requestsite(self, url)
    thread_tags = soup.find_all(class_="structItem-title")
    base_url = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(url))
    threads = []
    for x in thread_tags:
        y = x.find_all(href=True)
        for element in y:
            link = element["href"]
            if "threads/" in link:
                stripped = link[0: link.rfind("/") + 1]
                if base_url + stripped not in threads:
                    threads.append(base_url + stripped)
    return threads


class XenforoConnector(LoadConnector):
    # track the initial run
    initial_run = True

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.last_run_date = datetime.utcnow().replace(tzinfo=pytz.utc) - timedelta(days=1)
        self.cookies = {}
        # mimic user browser to avoid being blocked by the website (see: https://www.useragents.me/)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        if credentials:
            logger.warning("Unexpected credentials provided for Xenforo Connector")
        return None

    def load_from_state(self) -> GenerateDocumentsOutput:
        # Standardize URL to always end in /.
        if self.base_url[-1] != "/":
            self.base_url += "/"

        # Remove all extra parameters from the end such as page, post.
        matches = ("threads/", "boards/")
        for each in matches:
            if each in self.base_url:
                try:
                    self.base_url = self.base_url[0: self.base_url.index("/", self.base_url.index(each) + len(each)) + 1]
                except ValueError:
                    pass

        doc_batch: list[Document] = []
        # Input is a forum thread_list_page, find all threads in this thread_list_page and scrape them.
        if "boards/" or "forums/" in self.base_url:
            all_threads = []
            pages = get_pages(requestsite(self, self.base_url), self.base_url)

            # Get all pages on thread_list_page
            for pre_count, thread_list_page in enumerate(pages, start=1):
                logger.info(
                    f"\x1b[KGetting pages from thread_list_page.. Current: {pre_count}/{len(pages)}\r"
                )
                all_threads += get_threads(self, thread_list_page)

            # Getting all threads from thread_list_page pages
            for thread_count, thread in enumerate(all_threads, start=1):
                soup = requestsite(self, thread)
                pages = get_pages(soup, thread)
                # Getting all pages for all threads
                for page_count, page in enumerate(pages, start=1):
                    logger.info(
                        f"\x1b[KProgress: Page {page_count}/{len(pages)} - Thread {thread_count}/{len(all_threads)}\r"
                    )
                    doc_batch.extend(scrape_page_posts(requestsite(self, page), thread, self.last_run_date))
                XenforoConnector.initial_run = False
                yield doc_batch
        # If the URL contains "threads/", scrape the thread
        if "threads/" in self.base_url:
            soup = requestsite(self, self.base_url)
            if soup is None:
                logger.error(f"Failed to load page: {self.base_url}")
                yield doc_batch

            pages = get_pages(soup, self.base_url)
            for page_count, page in enumerate(pages, start=1):
                soup = requestsite(self, self.base_url + "page-" + str(page_count))
                if soup is None:
                    logger.error(
                        f"Failed to load page: {self.base_url + 'page-' + str(page_count)}"
                    )
                    continue

                doc_batch.extend(scrape_page_posts(soup, page, self.last_run_date))
                XenforoConnector.initial_run = False
                yield doc_batch
        # If there are any documents to yield after the initial run, do so
        if doc_batch:
            yield doc_batch
