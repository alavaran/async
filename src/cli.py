
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Async Web Crawler",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file",
    )

    parser.add_argument(
        "--urls",
        nargs="+",
        default=None,
        help="Starting URLs",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to crawl",
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum crawling depth",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Directory for exported reports",
    )

    parser.add_argument(
        "--respect-robots",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Respect robots.txt",
    )

    parser.add_argument(
        "--rate-limit",
        type=float,
        default=None,
        help="Maximum requests per second",
    )

    return parser.parse_args()