# Async Web Crawler

An asynchronous, configurable web crawler built with Python and aiohttp. Supports concurrent crawling, rate limiting, robots.txt compliance, retry strategies, persistent storage, monitoring, and report generation.

## Features

- **Asynchronous crawling** — concurrent HTTP requests using asyncio and aiohttp.
- **Concurrency control** — global and per-domain request limits.
- **Rate limiting** — configurable requests per second, delays, and jitter.
- **Robots.txt support** — respects website crawling rules.
- **Retry mechanism** — configurable retries, timeouts, and exponential backoff.
- **URL filtering** — include/exclude patterns and domain restrictions.
- **Persistent storage** — SQLite, JSON, and CSV storage backends.
- **Configuration** — YAML-based configuration and CLI overrides.
- **Statistics and monitoring** — pages processed, success/failure rates, throughput, ETA, and active tasks.
- **Report generation** — JSON exports and HTML summary reports.
- **Sitemap parsing** — support for extracting URLs from XML sitemaps.

## Project Structure

```text
async/
├── config.yaml
├── main.py
├── benchmark.py
├── benchmark_concurrency.py
├── requirements.txt
├── requirements-dev.txt
├── src/
│   ├── advanced_crawler.py
│   ├── crawler.py
│   ├── config.py
│   ├── cli.py
│   ├── parser.py
│   ├── queue.py
│   ├── rate_limiter.py
│   ├── retry_strategy.py
│   ├── robots_parser.py
│   ├── semaphore_manager.py
│   ├── sitemap.py
│   ├── stats.py
│   ├── storage.py
│   ├── exporter.py
│   ├── monitor.py
│   ├── logging_config.py
│   └── exceptions.py
├── tests/
└── reports/
```

## Installation

Requires Python 3.10 or newer.

Clone the repository:

```bash
git clone https://github.com/alavaran/async
cd async
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Configuration

The crawler uses `config.yaml` for its settings.

Example:

```yaml
max_concurrent: 3
max_per_domain: 3
requests_per_second: 1.0

respect_robots: true
min_delay: 0.5
jitter: 0.0

max_retries: 3
connect_timeout: 10.0
read_timeout: 10.0
total_timeout: 20.0
backoff_base: 1.0

user_agent: "MyBot/1.0"

start_urls:
  - "https://books.toscrape.com/"

max_pages: 100
max_depth: 2
same_domain_only: true

include_patterns: []

exclude_patterns:
  - '\.pdf$'

storage:
  type: sqlite
  path: crawler.db
```

### Configuration parameters

| Parameter | Description |
|---|---|
| `max_concurrent` | Maximum number of concurrent tasks |
| `max_per_domain` | Maximum concurrent tasks per domain |
| `requests_per_second` | Request rate limit |
| `respect_robots` | Whether to respect robots.txt |
| `min_delay` | Minimum delay between requests |
| `jitter` | Randomized delay component |
| `max_retries` | Maximum retry attempts |
| `connect_timeout` | Connection timeout |
| `read_timeout` | Response read timeout |
| `total_timeout` | Total request timeout |
| `backoff_base` | Retry backoff base |
| `user_agent` | HTTP User-Agent header |
| `start_urls` | Initial URLs |
| `max_pages` | Maximum number of pages to process |
| `max_depth` | Maximum crawling depth |
| `same_domain_only` | Restrict crawling to starting domains |
| `include_patterns` | URL inclusion regex patterns |
| `exclude_patterns` | URL exclusion regex patterns |
| `storage` | Storage backend configuration |

## Usage

Run with the default configuration:

```bash
python main.py
```

Specify a configuration file:

```bash
python main.py --config config.yaml
```

Override crawling limits:

```bash
python main.py --max-pages 100 --max-depth 3
```

Specify a custom report directory:

```bash
python main.py --output-dir reports
```

Combine CLI arguments:

```bash
python main.py \
  --config config.yaml \
  --max-pages 100 \
  --max-depth 3 \
  --output-dir reports
```

CLI overrides apply only to the current execution and do not modify the original YAML file.

Display available options:

```bash
python main.py --help
```

## Monitoring and Reports

During execution, the crawler periodically logs monitoring information:

- Completed pages
- Total pages
- Progress percentage
- Elapsed time
- Pages per second
- Estimated time remaining
- Active tasks

After crawling, reports are exported to the configured output directory:

| File | Description |
|---|---|
| `crawl_results.json` | Crawled page results |
| `crawler_stats.json` | Aggregated crawler statistics |
| `error_report.json` | Error statistics |
| `crawler_report.html` | HTML summary report |

## Testing

Run the complete test suite:

```bash
python -m pytest -v
```

## Benchmarking

Run a basic performance benchmark:

```bash
python benchmark.py
```

Compare different concurrency levels:

```bash
python benchmark_concurrency.py
```

The concurrency benchmark compares execution time and throughput for different worker counts.

### Performance Benchmark

The crawler was benchmarked against a sequential synchronous implementation using a local HTTP server to eliminate external network variability.

Each configuration was tested 5 times. Median execution time, throughput, and peak Python memory allocations were measured.

| Pages | Mode | Workers | Pages/sec | Memory (MB) | Speedup |
|---:|---|---:|---:|---:|---:|
| 100 | Sync | 1 | 373.76 | 0.61 | 1.00x |
| 100 | Async | 5 | 472.50 | 1.14 | 1.26x |
| 500 | Sync | 1 | 381.12 | 1.15 | 1.00x |
| 500 | Async | 20 | 375.61 | 4.21 | 0.99x |
| 1000 | Sync | 1 | 372.28 | 1.61 | 1.00x |
| 1000 | Async | 20 | 383.82 | 4.88 | 1.03x |

**Conclusions:**
- All benchmark scenarios completed successfully with zero failed pages.
- Async crawling achieved its best relative improvement on the 100-page workload (1.26x).
- For 500 and 1000 pages, async and synchronous throughput was nearly identical in the local test environment.
- Higher concurrency increased memory allocations without providing a consistent throughput improvement.
- Async crawling is expected to provide greater benefits in real-world environments with higher network latency and multiple domains.

**Limitations:** The benchmark uses a local HTTP server and measures Python memory allocations with `tracemalloc`, not total process memory. Results may differ significantly on real websites.


## Technologies

- Python
- asyncio
- aiohttp
- BeautifulSoup
- SQLite / aiosqlite
- PyYAML
- pytest

## Disclaimer

Use the crawler responsibly. Respect website terms of service, robots.txt directives, rate limits, and applicable laws.
