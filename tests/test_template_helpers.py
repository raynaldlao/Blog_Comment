from datetime import UTC, datetime

import pytest
from flask import render_template_string
from jinja2.exceptions import TemplateNotFound
from markupsafe import Markup

from utils.template_helpers import date_format_filter, date_iso_filter, nl2br_filter


class TestIconMacro:
    """Tests for the icon() Jinja macro (inline SVG rendering)."""

    def test_renders_svg_with_icon_class(self, app_with_db):
        """icon('home') renders <span class="icon"><svg>."""
        with app_with_db.app_context():
            result = render_template_string(
                '{% from "macros/icons.html" import icon %}{{ icon("home") }}'
            )
        assert '<span class="icon">' in result
        assert "<svg" in result
        assert "viewBox=" in result

    def test_passes_extra_class(self, app_with_db):
        """icon('home', 'my-class') adds the class to <span class="icon my-class">."""
        with app_with_db.app_context():
            result = render_template_string(
                '{% from "macros/icons.html" import icon %}'
                '{{ icon("home", "my-class") }}'
            )
        assert 'class="icon my-class"' in result

    def test_unknown_icon_raises_error(self, app_with_db):
        """icon('nonexistent') raises TemplateNotFound — no silent failure."""
        with app_with_db.app_context():
            with pytest.raises(TemplateNotFound):
                render_template_string(
                    '{% from "macros/icons.html" import icon %}'
                    '{{ icon("nonexistent") }}'
                )


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


class TestFormatDatetimeLocaleFilter:
    """Tests for the format_datetime_locale Jinja2 filter."""

    def test_formats_datetime_in_default_locale(self, app_with_db):
        from flask import render_template_string
        dt = datetime(2023, 1, 27, 12, 0, 0)
        with app_with_db.app_context():
            result = render_template_string(
                "{{ dt|format_datetime_locale }}", dt=dt
            )
        assert result == "27 January 2023 à 13:00"

    def test_returns_empty_string_for_none(self, app_with_db):
        from flask import render_template_string
        with app_with_db.app_context():
            result = render_template_string(
                "{{ dt|format_datetime_locale }}", dt=None
            )
        assert result == ""

    def test_formats_datetime_with_custom_format(self, app_with_db):
        from flask import render_template_string
        dt = datetime(2023, 6, 15, 8, 30)
        with app_with_db.app_context():
            result = render_template_string(
                '{{ dt|format_datetime_locale("d MMMM yyyy") }}', dt=dt
            )
        assert result == "15 June 2023"

    def test_converts_utc_to_paris_timezone(self, app_with_db):
        from flask import render_template_string
        dt = datetime(2023, 1, 27, 12, 0, 0, tzinfo=UTC)
        with app_with_db.app_context():
            result = render_template_string(
                "{{ dt|format_datetime_locale }}", dt=dt
            )
        assert result == "27 January 2023 à 13:00"

    def test_formats_in_french_locale(self, app_with_db):
        from flask import render_template_string
        dt = datetime(2023, 1, 27, 12, 0, 0)
        with app_with_db.app_context():
            app_with_db.extensions["babel"].locale_selector = lambda: "fr"
            result = render_template_string(
                "{{ dt|format_datetime_locale }}", dt=dt
            )
        assert result == "27 janvier 2023 à 13:00"
