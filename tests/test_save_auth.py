"""
Unit tests for scripts/save_auth module
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import scripts.save_auth as mod


@pytest.fixture
def mock_auth_dir(tmp_path, monkeypatch):
    """Fixture: temporarily set AUTH_DIR to a temporary directory."""
    monkeypatch.setattr(mod, "AUTH_DIR", tmp_path)
    return tmp_path


class TestSaveAuth:
    """Tests for the save_auth() function."""

    def _mock_playwright_with_cookies(self, cookies):
        """Helper: Create Playwright mock chain with specified cookies."""
        context = MagicMock()
        context.cookies.return_value = cookies
        page = MagicMock()
        context.new_page.return_value = page
        browser = MagicMock()
        browser.new_context.return_value = context
        p = MagicMock()
        p.chromium.launch.return_value = browser
        return p, browser, context, page

    @patch("scripts.save_auth.sync_playwright")
    @patch("builtins.input", return_value="")
    def test_saves_session_when_cookies_found(self, mock_input, mock_playwright_cls, mock_auth_dir):
        cookies = [{"name": "session", "value": "abc123"}]
        p, browser, context, _ = self._mock_playwright_with_cookies(cookies)
        mock_playwright_cls.return_value.__enter__.return_value = p

        mod.save_auth("https://example.com", "mysite")

        expected_path = mock_auth_dir / "mysite.json"
        context.storage_state.assert_called_once_with(path=str(expected_path))
        browser.close.assert_called_once()

    @patch("scripts.save_auth.sync_playwright")
    @patch("builtins.input", side_effect=["", "n"])
    def test_aborts_when_no_cookies_and_user_declines_retry(self, mock_input, mock_playwright_cls, mock_auth_dir):
        p, browser, context, _ = self._mock_playwright_with_cookies([])
        mock_playwright_cls.return_value.__enter__.return_value = p

        mod.save_auth("https://example.com", "mysite")

        context.storage_state.assert_not_called()
        browser.close.assert_called_once()

    @patch("scripts.save_auth.sync_playwright")
    @patch("builtins.input", side_effect=["", "y", "", "n"])
    def test_retries_multiple_times_then_aborts(self, mock_input, mock_playwright_cls, mock_auth_dir):
        p, _, context, _ = self._mock_playwright_with_cookies([])
        mock_playwright_cls.return_value.__enter__.return_value = p

        mod.save_auth("https://example.com", "mysite")

        assert mock_input.call_count == 4
        context.storage_state.assert_not_called()

    @patch("scripts.save_auth.sync_playwright")
    @patch("builtins.input", side_effect=["", "y", ""])
    def test_saves_session_after_retry_succeeds(self, mock_input, mock_playwright_cls, mock_auth_dir):
        p, _, context, _ = self._mock_playwright_with_cookies([])
        mock_playwright_cls.return_value.__enter__.return_value = p
        context.cookies.side_effect = [[], [{"name": "session", "value": "abc"}]]

        mod.save_auth("https://example.com", "mysite")

        context.storage_state.assert_called_once()

    @patch("scripts.save_auth.sync_playwright")
    @patch("builtins.input", return_value="")
    def test_creates_auth_dir_if_missing(self, mock_input, mock_playwright_cls, tmp_path):
        # Arrange
        nested_dir = tmp_path / "nested" / "auth"
        original = mod.AUTH_DIR
        mod.AUTH_DIR = nested_dir

        try:
            p, _, context, _ = self._mock_playwright_with_cookies([{"name": "session"}])
            mock_playwright_cls.return_value.__enter__.return_value = p

            # Act
            mod.save_auth("https://example.com", "mysite")

            # Assert
            assert nested_dir.exists()
        finally:
            mod.AUTH_DIR = original

    @patch("scripts.save_auth.sync_playwright")
    @patch("builtins.input", return_value="")
    def test_navigates_to_provided_url(self, mock_input, mock_playwright_cls, mock_auth_dir):
        # Arrange
        url = "https://notebooklm.google.com"
        _, _, _, page = self._mock_playwright_with_cookies([{"name": "s"}])
        p = MagicMock()
        p.chromium.launch.return_value.new_context.return_value.new_page.return_value = page
        mock_playwright_cls.return_value.__enter__.return_value = p

        # Act
        mod.save_auth(url, "notebooklm")

        # Assert
        page.goto.assert_called_once_with(url)

    @patch("scripts.save_auth.sync_playwright")
    @patch("builtins.input", return_value="")
    def test_browser_launched_in_headful_mode(self, mock_input, mock_playwright_cls, mock_auth_dir):
        p, _, _, _ = self._mock_playwright_with_cookies([{"name": "s"}])
        mock_playwright_cls.return_value.__enter__.return_value = p

        mod.save_auth("https://example.com", "mysite")

        p.chromium.launch.assert_called_once_with(headless=False)


class TestSaveAuthMain:
    """Tests for the main() CLI entry point."""

    @patch("scripts.save_auth.save_auth")
    def test_main_parses_url_and_name(self, mock_save_auth):
        argv = ["save_auth.py", "--url", "https://example.com", "--name", "mysite"]

        with patch.object(sys, "argv", argv):
            mod.main()
        mock_save_auth.assert_called_once_with("https://example.com", "mysite")

    @patch("scripts.save_auth.save_auth")
    def test_main_fails_without_url(self, mock_save_auth):
        argv = ["save_auth.py", "--name", "mysite"]

        with patch.object(sys, "argv", argv):
            with pytest.raises(SystemExit):
                mod.main()

    @patch("scripts.save_auth.save_auth")
    def test_main_fails_without_name(self, mock_save_auth):
        argv = ["save_auth.py", "--url", "https://example.com"]

        with patch.object(sys, "argv", argv):
            with pytest.raises(SystemExit):
                mod.main()
