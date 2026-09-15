from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dendai_skills.scraper import ScrapeConfig, scrape_to_file


class ScraperTest(unittest.TestCase):
    def test_scrape_local_html_to_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "sample.html"
            output = root / "items.json"
            source.write_text(
                """
                <html>
                  <body>
                    <a class="item" href="/one">One</a>
                    <a class="item" href="/two">Two</a>
                  </body>
                </html>
                """,
                encoding="utf-8",
            )

            result = scrape_to_file(
                ScrapeConfig(
                    source=str(source),
                    selector="a.item",
                    attr="href",
                ),
                output,
            )

            saved = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(len(result.items), 2)
        self.assertEqual(saved["items"][0]["text"], "One")
        self.assertEqual(saved["items"][0]["value"], "/one")


if __name__ == "__main__":
    unittest.main()
