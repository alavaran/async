import logging

from urllib.parse import urljoin
from bs4 import BeautifulSoup


class HTMLParser:
    def parse(self, html: str) -> dict[str, str]:
        soup = BeautifulSoup(html, "lxml")

        table = soup.find("table", class_="table-striped")

        if table is None:
            return {}

        data = {}

        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])

            if len(cells) != 2:
                continue

            key = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)

            data[key] = value

        return {
            "upc": data.get("UPC", ""),
            "product_type": data.get("Product Type", ""),
            "price_excl_tax": data.get("Price (excl. tax)", ""),
            "price_inc_tax": data.get("Price (incl. tax)", ""),
            "tax": data.get("Tax", ""),
            "availability": data.get("Availability", ""),
            "num_reviews": data.get("Number of reviews", ""),
        }

    def get_book_urls(
        self,
        html: str,
        base_url: str = "http://books.toscrape.com/",
    ) -> list[str]:
        soup = BeautifulSoup(html, "lxml")

        urls = []

        for link in soup.select("article.product_pod h3 a"):
            href = link.get("href")

            if href:
                urls.append(urljoin(base_url, href))

        return urls    

    def extract_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
        internal_only: bool = False,
    ) -> list[str]:
        from urllib.parse import urljoin, urlparse

        base_parsed = urlparse(base_url)

        if base_parsed.scheme not in ("http", "https") or not base_parsed.netloc:
            return []

        links = []

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()

            if not href:
                continue

            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)

            if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
                continue

            if internal_only and parsed_url.netloc != base_parsed.netloc:
                continue

            links.append(absolute_url)

        return list(dict.fromkeys(links))
    
    def extract_text(
        self,
        soup: BeautifulSoup,
        selector: str = None,
    ) -> str:
        if selector:
            element = soup.select_one(selector)
            if element is None:
                return ""
            return element.get_text(" ", strip=True)

        return soup.get_text(" ", strip=True)

    
    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        title_tag = soup.find("title")
        description_tag = soup.find("meta", attrs={"name": "description"})
        keywords_tag = soup.find("meta", attrs={"name": "keywords"})

        return {
            "title": title_tag.get_text(strip=True) if title_tag else "",
            "description": (
                description_tag.get("content", "")
                if description_tag else ""
            ),
            "keywords": (
                keywords_tag.get("content", "")
                if keywords_tag else ""
            ),
        }

    
    async def parse_html(self, html: str, url: str) -> dict:
        try:
            soup = BeautifulSoup(html, "lxml")

            return {
                "url": url,
                "title": (
                    soup.title.get_text(strip=True)
                    if soup.title else ""
                ),
                "text": self.extract_text(soup),
                "links": self.extract_links(soup, url),
                "metadata": self.extract_metadata(soup),
                "images": self.extract_images(soup),
                "headings": self.extract_headings(soup),
                "tables": self.extract_tables(soup),
                "lists": self.extract_lists(soup),
            }


        except Exception as error:
            logging.warning(
                "Ошибка парсинга HTML для %s: %s",
                url,
                error,
            )

            return {
                "url": url,
                "title": "",
                "text": "",
                "links": [],
                "metadata": {
                    "title": "",
                    "description": "",
                    "keywords": "",
                },
            }

    
    def extract_images(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        images = []

        for img in soup.find_all("img"):
            images.append({
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
            })

        return images

    def extract_headings(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        headings = []

        for tag in soup.find_all(["h1", "h2", "h3"]):
            headings.append({
                "tag": tag.name,
                "text": tag.get_text(" ", strip=True),
            })

        return headings

    def extract_tables(self, soup: BeautifulSoup) -> list[list[list[str]]]:
        tables = []

        for table in soup.find_all("table"):
            rows = []

            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                rows.append([
                    cell.get_text(" ", strip=True)
                    for cell in cells
                ])

            tables.append(rows)

        return tables

    def extract_lists(self, soup: BeautifulSoup) -> list[dict[str, object]]:
        lists = []

        for tag in soup.find_all(["ul", "ol"]):
            items = [
                item.get_text(" ", strip=True)
                for item in tag.find_all("li", recursive=False)
            ]

            lists.append({
                "type": tag.name,
                "items": items,
            })

        return lists

