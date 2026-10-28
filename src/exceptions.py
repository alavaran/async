
class CrawlerError(Exception):
    """Base exception for crawler errors."""


class TransientError(CrawlerError):
    """Temporary HTTP errors, such as 429, 500 and 503."""


class PermanentError(CrawlerError):
    """Permanent HTTP errors, such as 401, 403 and 404."""


class NetworkError(CrawlerError):
    """Network connection and DNS errors."""


class ParseError(CrawlerError):
    """Errors encountered while parsing page content."""
