from bs4 import BeautifulSoup
from urllib.parse import urljoin

class BookParser:
    def parse(self, html: str) -> dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")

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

class BookParser:
    def parse(self, html: str) -> dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")

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
        base_url: str = "http://books.toscrape.com/"
    ) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")

        urls = []

        for link in soup.select("article.product_pod h3 a"):
            href = link.get("href")

            if href:
                urls.append(urljoin(base_url, href))

        return urls