import json
import os
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from babel.dates import format_datetime
from flask_babel import get_locale
from markupsafe import Markup, escape


class ViteManifest:
    """
    Reads the Vite build manifest to resolve hashed asset filenames.

    Reads the manifest file on every call so that rebuilds (which change
    file hashes) take effect without restarting Flask.
    """
    _manifest_path: str | None = None

    @classmethod
    def init(cls, static_dir: str | None) -> None:
        if static_dir is None:
            raise RuntimeError("Flask static_folder is None; cannot locate Vite manifest.")
        cls._manifest_path = os.path.join(static_dir, ".vite", "manifest.json")

    @classmethod
    def _load(cls) -> dict:
        if cls._manifest_path and os.path.exists(cls._manifest_path):
            with open(cls._manifest_path) as f:
                return json.load(f)
        return {}

    @classmethod
    def get(cls, entry: str = "core/entry.jsx") -> dict:
        manifest = cls._load()
        return manifest.get(entry, {})

    @classmethod
    def get_js(cls, entry: str = "core/entry.jsx") -> str | None:
        data = cls.get(entry)
        return data.get("file")

    @classmethod
    def get_css(cls, entry: str = "core/entry.jsx") -> list[str]:
        data = cls.get(entry)
        css = list(data.get("css", []) or [])
        for imp in data.get("imports", []):
            imp_data = cls._load().get(imp, {})
            css.extend(imp_data.get("css", []) or [])
        return css

    @classmethod
    def get_vendor_js(cls) -> str | None:
        manifest = cls._load()
        for entry_data in manifest.values():
            path = entry_data.get("file", "")
            if path.startswith("assets/vendor-") and path.endswith(".js"):
                return path
        return None

def nl2br_filter(text: str | None) -> str:
    """
    Jinja2 filter that escapes HTML and converts newlines to <br> tags.

    Safely renders user-generated text by first escaping all HTML,
    then replacing newline characters with HTML line break tags.
    The result is marked as safe HTML to prevent double-escaping.

    Args:
        text: Raw user input string, or None.

    Returns:
        An escaped string with \\n replaced by <br>\\n, marked as safe HTML.
        Returns empty string if input is None or empty.
    """
    if not text:
        return ""
    escaped = escape(text)
    return Markup(str(escaped).replace("\n", "<br>\n"))


def inject_vite_assets() -> dict:
    """
    Context processor that injects Vite-built asset URLs into the
    template rendering context.

    Reads the Vite manifest to resolve hashed filenames for the
    BlockNote React frontend bundle.

    Returns:
        dict: Contains ``vite_js_url`` (str or None) and
        ``vite_css_urls`` (list of str) pointing to hashed assets
        under the ``dist/`` subdirectory.
    """
    js_file = ViteManifest.get_js()
    css_files = ViteManifest.get_css()
    vendor_js = ViteManifest.get_vendor_js()
    VITE_PREFIX = "dist/"
    return {
        "vite_js_url": VITE_PREFIX + js_file if js_file else None,
        "vite_css_urls": [VITE_PREFIX + f for f in css_files] if css_files else [],
        "vite_vendor_js_url": VITE_PREFIX + vendor_js if vendor_js else None,
    }


def inject_current_year() -> dict[str, int]:
    """
    Context processor that injects the current calendar year into the
    template rendering context.

    Used by the base layout to display a dynamic copyright year in the
    footer, eliminating the need to pass the year manually in every
    ``render_template()`` call.

    Returns:
        dict[str, int]: A single-entry dictionary with key ``"current_year"``
        mapped to the current UTC year (e.g. ``{"current_year": 2026}``).
    """
    return {"current_year": datetime.now(UTC).year}


def date_format_filter(date: datetime | None, format: str = "%b %d, %Y") -> str:
    """
    Jinja2 filter that formats a datetime into a human-readable date string.

    Args:
        date: A datetime object to format, or None.
        format: A strftime format string (default: ``"%b %d, %Y"``).

    Returns:
        The formatted date string (e.g. ``"Apr 29, 2026"``).
        Returns ``"RECENT"`` if the input is None.
    """
    if date is None:
        return "RECENT"
    return date.strftime(format)


def format_datetime_locale(date: datetime | None, format: str = "d MMMM yyyy 'à' HH:mm") -> str:
    """
    Jinja2 filter that formats a UTC datetime to Europe/Paris local time
    using Flask-Babel's locale-aware formatting.

    Respects the current application locale (fr, en, etc.) via
    ``flask_babel.get_locale()``. Falls back to UTC if the datetime is naive.

    Args:
        date: A UTC datetime object to format, or None.
        format: A Babel format string (default: ``"d MMMM yyyy 'à' HH:mm"``).

    Returns:
        The formatted date string (e.g. ``"22 juillet 2026 à 10:54"`` in French,
        ``"22 July 2026 à 10:54"`` in English). Returns empty string if date is None.
    """
    if date is None:
        return ""
    if date.tzinfo is None:
        date = date.replace(tzinfo=ZoneInfo("UTC"))
    local = date.astimezone(ZoneInfo("Europe/Paris"))
    locale = get_locale()
    return format_datetime(local, format=format, locale=locale)


def date_iso_filter(date: datetime | None) -> str:
    """
    Jinja2 filter that formats a datetime as an ISO 8601 date string.

    Suitable for use in the ``datetime`` attribute of HTML ``<time>``
    elements to provide machine-readable dates.

    Args:
        date: A datetime object to format, or None.

    Returns:
        The date formatted as ``"YYYY-MM-DD"`` (e.g. ``"2026-05-16"``).
        Returns an empty string if the input is None.
    """
    if date is None:
        return ""
    return date.strftime("%Y-%m-%d")
