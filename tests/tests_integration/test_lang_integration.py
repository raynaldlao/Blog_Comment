import pytest


class TestLangSwitching:
    """Tests verifying language switching behaviour via POST /lang/<locale>."""

    @pytest.mark.parametrize("locale,expected_status,expected_lang", [
        ("fr", 302, "fr"),
        ("en", 302, "en"),
        ("de", 302, None),
    ])
    def test_set_lang(
        self, client, db_session, locale, expected_status, expected_lang
    ):
        """
        Verifies that POST /lang/<locale> sets the 'lang' session key
        for valid locales ('fr', 'en'), and silently ignores invalid ones.

        Steps:
            1. POST to /lang/<locale>.
            2. Assert redirect (302).
            3. Inspect session for 'lang' key.
        """
        resp = client.post(f"/lang/{locale}")
        assert resp.status_code == expected_status
        with client.session_transaction() as sess:
            if expected_lang is None:
                assert "lang" not in sess
            else:
                assert sess.get("lang") == expected_lang
