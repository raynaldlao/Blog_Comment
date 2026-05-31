"""Unit tests for template helper functions (filters, context processors)."""

from datetime import datetime

from markupsafe import Markup

from utils.template_helpers import date_format_filter, date_iso_filter, nl2br_filter


class TestNl2brFilter:
    """Unit tests for the nl2br Jinja2 filter."""

    def test_escapes_html_tags(self):
        result = nl2br_filter("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_converts_newlines_to_br(self):
        result = nl2br_filter("line1\nline2")
        assert "line1<br>\nline2" in result

    def test_handles_multiple_newlines(self):
        result = nl2br_filter("a\n\nb")
        assert str(result).count("<br>") == 2

    def test_returns_empty_for_none(self):
        assert nl2br_filter(None) == ""

    def test_returns_empty_for_empty_string(self):
        assert nl2br_filter("") == ""

    def test_returns_markup_instance(self):
        assert isinstance(nl2br_filter("test"), Markup)

    def test_does_not_escape_generated_br(self):
        result = nl2br_filter("hello\nworld")
        assert "<br>" in str(result)

    def test_handles_text_without_newlines(self):
        assert nl2br_filter("hello world") == "hello world"

    def test_escapes_ampersands(self):
        result = nl2br_filter("a & b")
        assert "&amp;" in result

    def test_escapes_quotes(self):
        result = nl2br_filter('say "hello"')
        assert "&#34;" in result
        assert '"' not in str(result)

    def test_mixed_content_with_newlines_and_html(self):
        result = nl2br_filter("<b>bold</b>\nnext line")
        assert "&lt;b&gt;bold&lt;/b&gt;" in result
        assert "<br>" in str(result)
        assert "<b>" not in str(result)


class TestDateFormatFilter:
    """Unit tests for the date_format Jinja2 filter."""

    def test_formats_date_with_default_format(self):
        result = date_format_filter(datetime(2026, 4, 29))
        assert result == "Apr 29, 2026"

    def test_returns_recent_for_none_date(self):
        result = date_format_filter(None)
        assert result == "RECENT"

    def test_uses_custom_format(self):
        result = date_format_filter(datetime(2026, 4, 29), "%Y-%m-%d")
        assert result == "2026-04-29"


class TestDateIsoFilter:
    """Tests for the date_iso Jinja2 filter."""

    def test_formats_date_to_iso_format(self):
        result = date_iso_filter(datetime(2026, 5, 16))
        assert result == "2026-05-16"

    def test_pads_single_digit_month_and_day(self):
        result = date_iso_filter(datetime(2026, 1, 1))
        assert result == "2026-01-01"

    def test_returns_empty_string_for_none(self):
        result = date_iso_filter(None)
        assert result == ""
