from datetime import UTC, datetime

from markupsafe import Markup, escape


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
