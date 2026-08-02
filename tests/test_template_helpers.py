from datetime import UTC, datetime

import pytest
from flask import render_template_string
from jinja2.exceptions import TemplateNotFound

from flask_setup.template_helpers import ViteManifest, date_iso_filter


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


class TestViteManifest:
    def test_init_with_none_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="Flask static_folder is None"):
            ViteManifest.init(None)

    def test_load_returns_empty_when_no_manifest(self):
        ViteManifest.init("/tmp")
        ViteManifest._manifest_path = "/tmp/.vite/manifest.json"
        result = ViteManifest._load()
        assert result == {}

    def test_get_vendor_js_returns_none_when_no_vendor(self, app_with_db, tmp_path):
        manifest_dir = tmp_path / ".vite"
        manifest_dir.mkdir()
        manifest = manifest_dir / "manifest.json"
        manifest.write_text('{"core/entry.jsx":{"file":"assets/index-abc123.js","css":["assets/index-abc123.css"]}}')
        ViteManifest._manifest_path = str(manifest)
        result = ViteManifest.get_vendor_js()
        assert result is None
