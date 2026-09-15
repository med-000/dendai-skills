from __future__ import annotations

import unittest

from dendai_skills.webclass import (
    extract_frame_urls,
    parse_detail_page,
    parse_lesson_contents,
)


DOCUMENT_DETAIL_HTML = """
<html>
  <body>
    <a class="course-name" href="/webclass/course.php/course/">情報通信理論</a>
    <h3 class="page-header">講義資料</h3>
    <p>種類 : 資料</p>
    <div class="contentsInfoList">
      <div class="contentsInfoListItem">
        <div class="contentsInfoListLabel">種別</div>
        <div class="contentsInfoListData">資料</div>
      </div>
    </div>
    <a href="/webclass/course.php/course/contents/content/exec">開始</a>
  </body>
</html>
"""

TEST_DETAIL_HTML = """
<html>
  <body>
    <h3 class="page-header">第1章 小テスト</h3>
    <p>種類 : 自習</p>
    <div class="contentsInfoList">
      <div class="contentsInfoListItem">
        <div class="contentsInfoListLabel">種別</div>
        <div class="contentsInfoListData">自習</div>
      </div>
      <div class="contentsInfoListItem">
        <div class="contentsInfoListLabel">日時制限</div>
        <div class="contentsInfoListData">2026/09/14 12:00 〜 2026/09/20 23:59</div>
      </div>
    </div>
  </body>
</html>
"""

LESSON_HTML = """
<html>
  <body>
    <section data-contents-id="875312c6193f29fb67d8f79f390281eb"
      data-contents-name="第1章 小テスト"
      data-end-date="1789916399"
      class="list-group-item cl-contentsList_listGroupItem">
      <h4 class="cm-contentsList_contentName">
        <a href="/webclass/do_contents.php?reset_status=1&amp;set_contents_id=875312c6193f29fb67d8f79f390281eb">第1章 小テスト</a>
      </h4>
      <div class="cl-contentsList_categoryLabel">自習</div>
      <div class="cm-contentsList_contentDetailListItem">
        <div class="cm-contentsList_contentDetailListItemLabel">利用可能期間</div>
        <div class="cm-contentsList_contentDetailListItemData">2026/09/14 12:00 - 2026/09/20 23:59</div>
      </div>
      <a href="/webclass/course.php/202611099528010201/contents/875312c6193f29fb67d8f79f390281eb/?acs_=token">詳細</a>
      <a href="/webclass/course.php/202611099528010201/contents/875312c6193f29fb67d8f79f390281eb/history?acs_=token">利用回数 1</a>
    </section>
  </body>
</html>
"""

DOCUMENT_FRAME_HTML = """
<html>
  <frameset rows="55,*">
    <frame src="title_simple.php?rnd=abc&amp;acs_=token" name="webclass_title">
    <frameset cols="0%,100%">
      <frame src="txtbk_show_chapter.php?rnd=abc&amp;acs_=token" name="webclass_chapter">
      <frame src="txtbk_show_text.php?contents_id=content&amp;acs_=token" name="webclass_content">
    </frameset>
  </frameset>
</html>
"""


class WebClassParserTest(unittest.TestCase):
    def test_parse_document_detail(self) -> None:
        detail = parse_detail_page(
            DOCUMENT_DETAIL_HTML,
            "https://els.sa.dendai.ac.jp/webclass/course.php/x/contents/y/",
        )

        self.assertEqual(detail.title, "講義資料")
        self.assertEqual(detail.kind, "資料")
        self.assertEqual(detail.fields["種別"], "資料")
        self.assertIn("開始", detail.links)

    def test_parse_test_detail_with_deadline(self) -> None:
        detail = parse_detail_page(
            TEST_DETAIL_HTML,
            "https://els.sa.dendai.ac.jp/webclass/course.php/x/contents/y/",
        )

        self.assertEqual(detail.title, "第1章 小テスト")
        self.assertEqual(detail.kind, "自習")
        self.assertEqual(detail.fields["日時制限"], "2026/09/14 12:00 〜 2026/09/20 23:59")

    def test_parse_lesson_contents(self) -> None:
        contents = parse_lesson_contents(
            LESSON_HTML,
            "https://els.sa.dendai.ac.jp/webclass/course.php/202611099528010201/",
        )

        self.assertEqual(len(contents), 1)
        first_test = next(content for content in contents if content.name == "第1章 小テスト")
        self.assertEqual(first_test.category, "自習")
        self.assertEqual(first_test.availability, "2026/09/14 12:00 - 2026/09/20 23:59")
        self.assertIsNotNone(first_test.detail_url)

    def test_extract_document_frame_urls(self) -> None:
        urls = extract_frame_urls(
            DOCUMENT_FRAME_HTML,
            "https://els.sa.dendai.ac.jp/webclass/",
        )

        self.assertTrue(any("txtbk_show_text.php" in url for url in urls))


if __name__ == "__main__":
    unittest.main()
