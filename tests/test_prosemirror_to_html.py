from markupsafe import Markup

from utils.prosemirror_to_html import prosemirror_to_html


class TestProsemirrorToHtml:
    def test_paragraph(self):
        result = prosemirror_to_html(
            '[{"type":"paragraph","content":[{"type":"text","text":"Hello world"}]}]'
        )
        assert result == Markup("<p>Hello world</p>")

    def test_heading_default_level(self):
        result = prosemirror_to_html(
            '[{"type":"heading","props":{"level":3},"content":[{"type":"text","text":"Subtitle"}]}]'
        )
        assert result == Markup("<h3>Subtitle</h3>")

    def test_bold_mark(self):
        result = prosemirror_to_html(
            '[{"type":"paragraph","content":[{"type":"text","marks":[{"type":"bold"}],"text":"bold text"}]}]'
        )
        assert result == Markup("<p><strong>bold text</strong></p>")

    def test_italic_mark(self):
        result = prosemirror_to_html(
            '[{"type":"paragraph","content":[{"type":"text","marks":[{"type":"italic"}],"text":"italic text"}]}]'
        )
        assert result == Markup("<p><em>italic text</em></p>")

    def test_nested_marks_bold_then_italic(self):
        result = prosemirror_to_html(
            '[{"type":"paragraph","content":[{"type":"text","marks":[{"type":"bold"},{"type":"italic"}],"text":"bold+italic"}]}]'
        )
        assert result == Markup("<p><strong><em>bold+italic</em></strong></p>")

    def test_link_mark(self):
        result = prosemirror_to_html(
            '[{"type":"paragraph","content":[{"type":"text","marks":[{"type":"link",'
            '"attrs":{"href":"https://example.com"}}],"text":"click here"}]}]'
        )
        assert result == Markup('<p><a href="https://example.com">click here</a></p>')

    def test_code_block_with_language(self):
        result = prosemirror_to_html(
            '[{"type":"codeBlock","props":{"language":"python"},"content":[{"type":"text","text":"print(42)"}]}]'
        )
        assert result == Markup(
            '<pre><code class="language-python">print(42)</code></pre>'
        )

    def test_code_block_no_language(self):
        result = prosemirror_to_html(
            '[{"type":"codeBlock","content":[{"type":"text","text":"plain code"}]}]'
        )
        assert result == Markup("<pre><code>plain code</code></pre>")

    def test_bullet_list(self):
        result = prosemirror_to_html(
            '[{"type":"bulletList","content":[{"type":"listItem","content":[{"type":"paragraph",'
            '"content":[{"type":"text","text":"Item 1"}]}]},{"type":"listItem","content":'
            '[{"type":"paragraph","content":[{"type":"text","text":"Item 2"}]}]}]}]'
        )
        assert "<ul>" in str(result)
        assert "<li>" in str(result)
        assert "Item 1" in str(result)

    def test_ordered_list(self):
        result = prosemirror_to_html(
            '[{"type":"orderedList","content":[{"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"First"}]}]}]}]'
        )
        assert "<ol>" in str(result)
        assert "<li>" in str(result)

    def test_blockquote(self):
        result = prosemirror_to_html(
            '[{"type":"blockquote","content":[{"type":"text","text":"Cited text"}]}]'
        )
        assert result == Markup("<blockquote>\nCited text\n</blockquote>")

    def test_horizontal_rule(self):
        result = prosemirror_to_html('[{"type":"horizontalRule"}]')
        assert result == Markup("<hr>")

    def test_image_with_caption(self):
        result = prosemirror_to_html(
            '[{"type":"image","props":{"url":"/uploads/photo.jpg","alt":"A photo","caption":"Sunset view"}}]'
        )
        assert "<figure>" in str(result)
        assert '<img src="/uploads/photo.jpg"' in str(result)
        assert "<figcaption>Sunset view</figcaption>" in str(result)

    def test_image_no_caption(self):
        result = prosemirror_to_html(
            '[{"type":"image","props":{"url":"/uploads/img.png","alt":"Image"}}]'
        )
        assert "<figure>" in str(result)
        assert "<figcaption>" not in str(result)

    def test_video_youtube_embed(self):
        result = prosemirror_to_html(
            '[{"type":"video","props":{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}}]'
        )
        assert '<a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ">' in str(result)

    def test_video_youtu_be_short(self):
        result = prosemirror_to_html(
            '[{"type":"video","props":{"url":"https://youtu.be/dQw4w9WgXcQ"}}]'
        )
        assert '<a href="https://youtu.be/dQw4w9WgXcQ">' in str(result)

    def test_video_non_youtube_link(self):
        result = prosemirror_to_html(
            '[{"type":"video","props":{"url":"https://vimeo.com/12345"}}]'
        )
        assert '<a href="https://vimeo.com/12345">Watch video</a>' in str(result)

    def test_video_no_url(self):
        result = prosemirror_to_html('[{"type":"video","props":{}}]')
        assert result == Markup("")

    def test_legacy_plain_text(self):
        result = prosemirror_to_html("Hello world, this is a legacy article.")
        assert result == Markup("<p>Hello world, this is a legacy article.</p>")

    def test_none_input(self):
        result = prosemirror_to_html(None)
        assert result == Markup("")

    def test_empty_list(self):
        result = prosemirror_to_html("[]")
        assert result == Markup("")

    def test_unknown_block_type_falls_back_to_paragraph(self):
        result = prosemirror_to_html(
            '[{"type":"unknownBlock","content":[{"type":"text","text":"fallback"}]}]'
        )
        assert result == Markup("<p>fallback</p>")

    def test_code_block_escapes_html(self):
        result = prosemirror_to_html(
            '[{"type":"codeBlock","content":[{"type":"text","text":"<script>alert(1)</script>"}]}]'
        )
        assert "&lt;script&gt;" in str(result)
        assert "<script>" not in str(result)

    def test_inline_code_mark(self):
        result = prosemirror_to_html(
            '[{"type":"paragraph","content":[{"type":"text","marks":[{"type":"code"}],"text":"var x = 1;"}]}]'
        )
        assert result == Markup("<p><code>var x = 1;</code></p>")

    def test_hard_break(self):
        result = prosemirror_to_html(
            '[{"type":"paragraph","content":[{"type":"text","text":"line1"},{"type":"hardBreak"},{"type":"text","text":"line2"}]}]'
        )
        assert result == Markup("<p>line1<br>line2</p>")

    def test_returns_markup_instance(self):
        result = prosemirror_to_html(
            '[{"type":"paragraph","content":[{"type":"text","text":"test"}]}]'
        )
        assert isinstance(result, Markup)

    def test_image_relative_url_with_base_url(self):
        result = prosemirror_to_html(
            '[{"type":"image","props":{"url":"/uploads/photo.jpg","alt":"Photo"}}]',
            base_url="http://example.com/"
        )
        assert 'src="http://example.com/uploads/photo.jpg"' in str(result)

    def test_image_absolute_url_unchanged_with_base_url(self):
        result = prosemirror_to_html(
            '[{"type":"image","props":{"url":"https://cdn.example.com/img.jpg"}}]',
            base_url="http://example.com/"
        )
        assert 'src="https://cdn.example.com/img.jpg"' in str(result)

    def test_image_no_base_url_leaves_relative(self):
        result = prosemirror_to_html(
            '[{"type":"image","props":{"url":"/uploads/photo.jpg"}}]'
        )
        assert 'src="/uploads/photo.jpg"' in str(result)

    def test_image_attrs_fallback_preserves_backward_compat(self):
        result = prosemirror_to_html(
            '[{"type":"image","attrs":{"url":"/legacy/img.jpg","alt":"Legacy"}}]'
        )
        assert 'src="/legacy/img.jpg"' in str(result)

    def test_heading_attrs_fallback_preserves_level(self):
        result = prosemirror_to_html(
            '[{"type":"heading","attrs":{"level":2},"content":[{"type":"text","text":"Legacy H2"}]}]'
        )
        assert result == Markup("<h2>Legacy H2</h2>")

    def test_code_block_attrs_fallback_preserves_language(self):
        result = prosemirror_to_html(
            '[{"type":"codeBlock","attrs":{"language":"javascript"},"content":[{"type":"text","text":"console.log(1)"}]}]'
        )
        assert '<code class="language-javascript">' in str(result)

    def test_video_attrs_fallback_preserves_url(self):
        result = prosemirror_to_html(
            '[{"type":"video","attrs":{"url":"https://example.com/video.mp4"}}]'
        )
        assert '<a href="https://example.com/video.mp4">' in str(result)
