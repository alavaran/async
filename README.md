# Async Web Crawler & HTML Parser

An asynchronous web crawler built with Python that fetches multiple web pages concurrently and extracts structured data from HTML.

The project demonstrates asynchronous programming with `asyncio`, HTTP requests with `aiohttp`, and HTML parsing with BeautifulSoup and `lxml`.

## Features

- **Asynchronous crawling** — fetch multiple URLs concurrently.
- **Concurrency control** — limit the number of simultaneous requests.
- **HTML parsing** — extract page titles, text, and metadata.
- **Link extraction** — resolve relative URLs and optionally filter external links.
- **Structured data extraction** — collect images, headings, tables, and lists.
- **Error handling** — handle HTTP errors, timeouts, and malformed HTML.
- **Automated tests** — verify crawler and parser behavior.
- **Performance comparison** — compare sequential and concurrent page fetching.

## Tech Stack

- Python 3.14
- `asyncio`
- `aiohttp`
- `BeautifulSoup4`
- `lxml`
- `unittest`

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/alavaran/async.git
cd async
```

### 2. Install dependencies

```bash
python -m pip install aiohttp beautifulsoup4 lxml
```

### 3. Run the crawler demo

```bash
python main.py
```

The demo fetches several pages from [Books to Scrape](https://books.toscrape.com/), parses their content, and prints statistics such as text length, number of links, images, and headings.

## Running Tests

Run the full test suite from the project root:

```bash
python -m unittest discover -s tests -v
```

## Project Structure

```text
async/
├── src/
│   ├── __init__.py
│   ├── crawler.py
│   └── parser.py
├── tests/
│   ├── test_crawler.py
│   └── test_parser.py
├── main.py
└── README.md
```

---
