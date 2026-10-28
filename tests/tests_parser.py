
import unittest
from src.parser import HTMLParser
from bs4 import BeautifulSoup

class TestHTMLParser(unittest.TestCase):

    def setUp(self):
        self.parser = HTMLParser()

    def test_extract_links_converts_relative_urls(self):
        html = """
        <a href="/books/">Books</a>
        <a href="https://example.com/page">Example</a>
        <a href="/books/">Duplicate</a>
        <a href="javascript:void(0)">Invalid</a>
        """

        soup = BeautifulSoup(html, "lxml")

        result = self.parser.extract_links(
            soup,
            "https://example.com/catalog/",
        )

        expected = [
            "https://example.com/books/",
            "https://example.com/page",
        ]

        self.assertEqual(result, expected)

    
    def test_extract_text_from_page(self):
        html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        soup = BeautifulSoup(html, "lxml")

        result = self.parser.extract_text(soup)

        self.assertEqual(result, "Hello World")

    def test_extract_text_by_selector(self):
        html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        soup = BeautifulSoup(html, "lxml")

        result = self.parser.extract_text(soup, "h1")

        self.assertEqual(result, "Hello")

    
    def test_extract_metadata(self):
        html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Page description">
                <meta name="keywords" content="python, html, parsing">
            </head>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")

        result = self.parser.extract_metadata(soup)

        self.assertEqual(result, {
            "title": "Test Page",
            "description": "Page description",
            "keywords": "python, html, parsing",
        })

    def test_extract_metadata_when_tags_missing(self):
        soup = BeautifulSoup("<html><body>Hello</body></html>", "lxml")

        result = self.parser.extract_metadata(soup)

        self.assertEqual(result, {
            "title": "",
            "description": "",
            "keywords": "",
        })

    
    def test_parse_html(self):
        html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Hello</h1>
                <a href="/books/">Books</a>
            </body>
        </html>
        """

        import asyncio

        result = asyncio.run(
            self.parser.parse_html(
                html,
                "https://example.com/catalog/",
            )
        )

        self.assertEqual(result["url"], "https://example.com/catalog/")
        self.assertEqual(result["title"], "Test Page")
        self.assertIn("Hello", result["text"])
        self.assertIn("https://example.com/books/", result["links"])
        self.assertEqual(result["metadata"]["description"], "Test description")

    
    def test_extract_images(self):
        html = """
        <img src="book.jpg" alt="Book">
        <img src="cover.png">
        """
        soup = BeautifulSoup(html, "lxml")

        result = self.parser.extract_images(soup)

        self.assertEqual(result, [
            {"src": "book.jpg", "alt": "Book"},
            {"src": "cover.png", "alt": ""},
        ])

    def test_extract_headings(self):
        html = """
        <h1>Books</h1>
        <h2>Fiction</h2>
        <h3>Adventure</h3>
        <h4>Ignored</h4>
        """
        soup = BeautifulSoup(html, "lxml")

        result = self.parser.extract_headings(soup)

        self.assertEqual(result, [
            {"tag": "h1", "text": "Books"},
            {"tag": "h2", "text": "Fiction"},
            {"tag": "h3", "text": "Adventure"},
        ])

    def test_extract_tables(self):
        html = """
        <table>
            <tr><th>Name</th><th>Price</th></tr>
            <tr><td>Book</td><td>10</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, "lxml")

        result = self.parser.extract_tables(soup)

        self.assertEqual(result, [
            [["Name", "Price"], ["Book", "10"]]
        ])

    def test_extract_lists(self):
        html = """
        <ul>
            <li>First</li>
            <li>Second</li>
        </ul>
        <ol>
            <li>Third</li>
        </ol>
        """
        soup = BeautifulSoup(html, "lxml")

        result = self.parser.extract_lists(soup)

        self.assertEqual(result, [
            {"type": "ul", "items": ["First", "Second"]},
            {"type": "ol", "items": ["Third"]},
        ])

    def test_extract_links_filters_external_and_invalid_urls(self):
        html = """
        <a href="/books/">Internal relative link</a>
        <a href="https://example.com/about">Internal absolute link</a>
        <a href="https://other.com/page">External link</a>
        <a href="javascript:void(0)">JavaScript link</a>
        <a href="mailto:test@example.com">Email link</a>
        """
        soup = BeautifulSoup(html, "lxml")

        result = self.parser.extract_links(
            soup,
            "https://example.com/catalog/",
            internal_only=True,
        )

        self.assertEqual(result, [
            "https://example.com/books/",
            "https://example.com/about",
        ])

    
    def test_parse_malformed_html(self):
        html = """
        <html>
            <head><title>Broken Page
            <body>
                <h1>Books without closing tags
                <a href="/books/">Books
                <img src="book.jpg" alt="Book">
        """

        import asyncio

        result = asyncio.run(
            self.parser.parse_html(
                html,
                "https://example.com/catalog/",
            )
        )

        self.assertEqual(result["url"], "https://example.com/catalog/")
        self.assertEqual(result["title"], "Broken Page")
        self.assertIn("Books without closing tags", result["text"])
        self.assertIn(
            "https://example.com/books/",
            result["links"],
        )
        self.assertEqual(
            result["images"],
            [{"src": "book.jpg", "alt": "Book"}],
        )

if __name__ == "__main__":
    unittest.main()

