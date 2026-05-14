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
