import json

from markupsafe import Markup, escape


def prosemirror_to_html(content_json: str | None, base_url: str = "") -> Markup:
    if not content_json:
        return Markup("")
    try:
        blocks = json.loads(content_json)
    except (json.JSONDecodeError, TypeError):
        return Markup(f"<p>{escape(content_json)}</p>")
    if not isinstance(blocks, list):
        return Markup("")
    parts = [_render_block(b, base_url) for b in blocks]
    return Markup("\n".join(parts))


def _render_block(block: dict, base_url: str = "") -> str:
    t = block.get("type", "")
    content = block.get("content") or []
    attrs = block.get("props") or block.get("attrs") or {}

    if t == "paragraph":
        return f"<p>{_render_inline(content)}</p>"

    if t == "heading":
        level = attrs.get("level", 2)
        level = max(1, min(6, level))
        return f"<h{level}>{_render_inline(content)}</h{level}>"

    if t == "bulletList":
        inner = "\n".join(_render_block(item, base_url) for item in content)
        return f"<ul>\n{inner}\n</ul>"

    if t == "orderedList":
        inner = "\n".join(_render_block(item, base_url) for item in content)
        return f"<ol>\n{inner}\n</ol>"

    if t == "listItem":
        inner = _render_list_item_content(content, base_url)
        return f"<li>\n{inner}\n</li>"

    if t == "codeBlock":
        lang = attrs.get("language", "")
        code_text = _extract_code_text(content)
        escaped_code = escape(code_text)
        if lang:
            return f'<pre><code class="language-{escape(lang)}">{escaped_code}</code></pre>'
        return f"<pre><code>{escaped_code}</code></pre>"

    if t == "blockquote":
        return f"<blockquote>\n{_render_inline(content)}\n</blockquote>"

    if t == "horizontalRule":
        return "<hr>"

    if t == "image":
        url = _abs_url(attrs.get("url", "") or "", base_url)
        alt = attrs.get("alt", "") or ""
        caption = attrs.get("caption", "") or ""
        img = f'<img src="{escape(url)}" alt="{escape(alt)}">'
        if caption:
            cap = f"<figcaption>{escape(caption)}</figcaption>"
            return f"<figure>\n{img}\n{cap}\n</figure>"
        return f"<figure>\n{img}\n</figure>"

    if t == "video":
        url = attrs.get("url", "") or ""
        if not url:
            return ""
        return f'<p><a href="{escape(url)}">Watch video</a></p>'

    if t == "checkListItem":
        inner = _render_list_item_content(content)
        if attrs.get("checked"):
            return f'<li class="checked">\n{inner}\n</li>'
        return f"<li>\n{inner}\n</li>"

    if t == "table":
        inner = "\n".join(_render_block(item, base_url) for item in content)
        return f"<table>\n{inner}\n</table>"

    if t in ("tableRow",):
        inner = "\n".join(_render_block(item, base_url) for item in content)
        return f"<tr>\n{inner}\n</tr>"

    if t in ("tableCell", "tableHeaderCell"):
        tag = "th" if t == "tableHeaderCell" else "td"
        return f"<{tag}>{_render_inline(content)}</{tag}>"

    return f"<p>{_render_inline(content)}</p>"


def _render_list_item_content(content: list, base_url: str = "") -> str:
    if not content:
        return ""
    first = content[0]
    if isinstance(first, dict) and first.get("type") == "text":
        return _render_inline(content)
    return "\n".join(_render_block(item, base_url) for item in content)


def _abs_url(url: str, base_url: str) -> str:
    if not url or url.startswith(("http://", "https://", "//")):
        return url
    if base_url and url.startswith("/"):
        return base_url.rstrip("/") + url
    return url


def _render_inline(content: list) -> str:
    if not content:
        return ""
    parts = []
    for node in content:
        if not isinstance(node, dict):
            continue
        nt = node.get("type")
        if nt == "text":
            text = node.get("text", "")
            marks = node.get("marks") or []
            parts.append(_render_marks(text, marks))
        elif nt == "hardBreak":
            parts.append("<br>")
    return "".join(parts)


def _render_marks(text: str, marks: list) -> str:
    if not marks:
        return escape(text)
    result = escape(text)
    for mark in reversed(marks):
        mt = mark.get("type", "")
        m_attrs = mark.get("attrs") or {}
        if mt == "bold":
            result = f"<strong>{result}</strong>"
        elif mt == "italic":
            result = f"<em>{result}</em>"
        elif mt == "underline":
            result = f"<u>{result}</u>"
        elif mt == "strike":
            result = f"<s>{result}</s>"
        elif mt == "link":
            href = m_attrs.get("href", "")
            result = f'<a href="{escape(href)}">{result}</a>'
        elif mt == "code":
            result = f"<code>{result}</code>"
        elif mt == "textColor":
            color = m_attrs.get("color", "")
            if color:
                result = f'<span style="color:{color}">{result}</span>'
        elif mt == "backgroundColor":
            bg = m_attrs.get("backgroundColor", "")
            if bg:
                result = f'<span style="background-color:{bg}">{result}</span>'
    return result


def _extract_code_text(content: list) -> str:
    parts = []
    for node in content or []:
        if isinstance(node, dict) and node.get("type") == "text":
            parts.append(node.get("text", ""))
    return "".join(parts)
