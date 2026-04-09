"""
Integration tests for PlaywrightExecutor

These tests launch a real browser and make real network requests.
Run them explicitly with:  pytest tests/test_playwright_executor_integration.py -v
Skip them in CI/fast runs with: pytest -m "not integration"
"""

import os
import pytest
from concurrent.futures import ThreadPoolExecutor

from src.playwright_executor import PlaywrightExecutor
from src.models import ActionType, Step


pytestmark = pytest.mark.integration


def _run(fn):
    """Run fn in a clean thread that has no running asyncio event loop."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(fn).result()


class TestPlaywrightExecutorIntegration:
    """Real browser tests against stable, public websites."""

    def test_navigate_to_example_com_and_extract_title(self):
        """Happy path: goto + extract_text works end-to-end."""
        steps = [
            Step(ActionType.GOTO,         {"url": "https://example.com"}),
            Step(ActionType.EXTRACT_TEXT, {"selector": "h1"}),
        ]

        def workflow():
            with PlaywrightExecutor(headless=True) as executor:
                return executor.execute_workflow(steps)

        results = _run(workflow)

        assert results[0].success is True
        assert results[0].data["url"] == "https://example.com"
        assert results[1].success is True
        assert results[1].data["text"] == "Example Domain"

    def test_navigate_and_extract_html(self):
        """extract_html returns raw HTML content of an element."""
        steps = [
            Step(ActionType.GOTO,         {"url": "https://example.com"}),
            Step(ActionType.EXTRACT_HTML, {"selector": "p:last-of-type"}),
        ]

        def workflow():
            with PlaywrightExecutor(headless=True) as executor:
                return executor.execute_workflow(steps)

        results = _run(workflow)

        assert results[0].success is True
        assert results[1].success is True
        assert "<a" in results[1].data["html"]  # the last paragraph contains the More information link

    def test_screenshot_saves_file(self, tmp_path):
        """screenshot handler actually writes the file to disk."""
        screenshot_path = str(tmp_path / "test_screenshot.png")
        steps = [
            Step(ActionType.GOTO,       {"url": "https://example.com"}),
            Step(ActionType.SCREENSHOT, {"path": screenshot_path}),
        ]

        def workflow():
            with PlaywrightExecutor(headless=True) as executor:
                return executor.execute_workflow(steps)

        results = _run(workflow)

        assert results[1].success is True
        assert results[1].data["path"] == screenshot_path
        assert os.path.exists(screenshot_path)
        assert os.path.getsize(screenshot_path) > 0

    def test_wait_for_element_that_exists(self):
        """wait_for succeeds when the element is already on the page."""
        steps = [
            Step(ActionType.GOTO,     {"url": "https://example.com"}),
            Step(ActionType.WAIT_FOR, {"selector": "h1"}),
        ]

        def workflow():
            with PlaywrightExecutor(headless=True) as executor:
                return executor.execute_workflow(steps)

        results = _run(workflow)

        assert results[0].success is True
        assert results[1].success is True

    def test_wait_for_element_that_does_not_exist_returns_failure(self):
        """wait_for returns failure (not exception) when element never appears."""
        steps = [
            Step(ActionType.GOTO,     {"url": "https://example.com"}),
            Step(ActionType.WAIT_FOR, {"selector": "#this-element-does-not-exist"}),
        ]

        def workflow():
            with PlaywrightExecutor(headless=True, timeout=3000) as executor:
                return executor.execute_workflow(steps)

        results = _run(workflow)

        assert results[0].success is True
        assert results[1].success is False
        assert results[1].error is not None

    def test_navigate_to_bad_url_returns_failure(self):
        """goto returns failure (not exception) for an unreachable URL."""
        steps = [
            Step(ActionType.GOTO, {"url": "https://this-domain-absolutely-does-not-exist-xyz.com"}),
        ]

        def workflow():
            with PlaywrightExecutor(headless=True, timeout=5000) as executor:
                return executor.execute_workflow(steps)

        results = _run(workflow)

        assert results[0].success is False
        assert results[0].error is not None
