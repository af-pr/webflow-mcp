"""
Unit tests for playwright_executor module

Note: These tests don't launch a real browser. The page object is replaced with
a MagicMock to verify that handlers call the correct Playwright methods with the
correct arguments.
"""

import pytest
from unittest.mock import MagicMock

from src.playwright_executor import PlaywrightExecutor
from src.models import ActionType, Step, Workflow


class TestPlaywrightExecutorInit:
    def test_default_values(self):
        executor = PlaywrightExecutor()
        assert executor.headless is True
        assert executor.timeout == 30000
        assert executor.auth_context_path is None

    def test_custom_config(self):
        executor = PlaywrightExecutor(auth_context_path="auth.json", headless=False, timeout=5000)
        assert executor.auth_context_path == "auth.json"
        assert executor.headless is False
        assert executor.timeout == 5000

    def test_all_action_types_are_registered(self):
        executor = PlaywrightExecutor()
        for action in ActionType:
            assert action in executor.actions

    def test_has_context_manager_interface(self):
        executor = PlaywrightExecutor()
        assert hasattr(executor, "__enter__")
        assert hasattr(executor, "__exit__")


class TestPlaywrightExecutorHandlers:
    """Handler tests: happy path verifies Playwright methods are called correctly,
    then error cases verify that Playwright failures return StepResult(success=False).
    """

    def setup_method(self):
        self.executor = PlaywrightExecutor()
        self.executor.page = MagicMock()

    # --- GOTO ---

    def test_goto_calls_page_goto_with_networkidle(self):
        step = Step(ActionType.GOTO, {"url": "https://example.com"})
        result = self.executor._handle_goto(step)

        self.executor.page.goto.assert_called_once_with("https://example.com", wait_until="networkidle")
        assert result.success is True
        assert result.data == {"url": "https://example.com"}

    def test_goto_playwright_error_returns_failure(self):
        self.executor.page.goto.side_effect = Exception("net::ERR_NAME_NOT_RESOLVED")
        step = Step(ActionType.GOTO, {"url": "https://bad.url"})
        result = self.executor._handle_goto(step)

        assert result.success is False
        assert "net::ERR_NAME_NOT_RESOLVED" in result.error

    # --- FILL ---

    def test_fill_calls_page_fill_with_selector_and_value(self):
        step = Step(ActionType.FILL, {"selector": "#username", "value": "alice"})
        result = self.executor._handle_fill(step)

        self.executor.page.fill.assert_called_once_with("#username", "alice")
        assert result.success is True
        assert result.data == {"selector": "#username"}

    def test_fill_playwright_error_returns_failure(self):
        self.executor.page.fill.side_effect = Exception("Element not found")
        step = Step(ActionType.FILL, {"selector": "#missing", "value": "text"})
        result = self.executor._handle_fill(step)

        assert result.success is False
        assert "Element not found" in result.error

    # --- CLICK ---

    def test_click_calls_page_click_with_selector(self):
        step = Step(ActionType.CLICK, {"selector": "#submit-btn"})
        result = self.executor._handle_click(step)

        self.executor.page.click.assert_called_once_with("#submit-btn")
        assert result.success is True
        assert result.data == {"selector": "#submit-btn"}

    def test_click_playwright_error_returns_failure(self):
        self.executor.page.click.side_effect = Exception("Timeout exceeded")
        step = Step(ActionType.CLICK, {"selector": "#btn"})
        result = self.executor._handle_click(step)

        assert result.success is False
        assert "Timeout exceeded" in result.error

    # --- SELECT ---

    def test_select_calls_page_select_option_with_selector_and_value(self):
        step = Step(ActionType.SELECT, {"selector": "#country", "value": "es"})
        result = self.executor._handle_select(step)

        self.executor.page.select_option.assert_called_once_with("#country", "es")
        assert result.success is True
        assert result.data == {"selector": "#country", "value": "es"}

    def test_select_playwright_error_returns_failure(self):
        self.executor.page.select_option.side_effect = Exception("Option not found")
        step = Step(ActionType.SELECT, {"selector": "#dropdown", "value": "invalid"})
        result = self.executor._handle_select(step)

        assert result.success is False
        assert "Option not found" in result.error

    # --- WAIT_FOR ---

    def test_wait_for_calls_page_wait_for_selector(self):
        step = Step(ActionType.WAIT_FOR, {"selector": ".spinner"})
        result = self.executor._handle_wait_for(step)

        self.executor.page.wait_for_selector.assert_called_once_with(".spinner")
        assert result.success is True
        assert result.data == {"selector": ".spinner"}

    def test_wait_for_playwright_timeout_returns_failure(self):
        self.executor.page.wait_for_selector.side_effect = Exception("Timeout 30000ms exceeded")
        step = Step(ActionType.WAIT_FOR, {"selector": ".never-appears"})
        result = self.executor._handle_wait_for(step)

        assert result.success is False
        assert "Timeout 30000ms exceeded" in result.error

    # --- EXTRACT_TEXT ---

    def test_extract_text_calls_page_text_content_and_returns_text(self):
        self.executor.page.text_content.return_value = "Hello World"
        step = Step(ActionType.EXTRACT_TEXT, {"selector": "h1"})
        result = self.executor._handle_extract_text(step)

        self.executor.page.text_content.assert_called_once_with("h1")
        assert result.success is True
        assert result.data == {"text": "Hello World"}

    def test_extract_text_returns_exact_text_without_modification(self):
        self.executor.page.text_content.return_value = "  raw text with spaces  "
        step = Step(ActionType.EXTRACT_TEXT, {"selector": "#content"})
        result = self.executor._handle_extract_text(step)

        assert result.data["text"] == "  raw text with spaces  "

    def test_extract_text_playwright_error_returns_failure(self):
        self.executor.page.text_content.side_effect = Exception("Selector not found")
        step = Step(ActionType.EXTRACT_TEXT, {"selector": "#missing"})
        result = self.executor._handle_extract_text(step)

        assert result.success is False
        assert "Selector not found" in result.error

    # --- EXTRACT_HTML ---

    def test_extract_html_calls_page_inner_html_and_returns_html(self):
        self.executor.page.inner_html.return_value = "<p>content</p>"
        step = Step(ActionType.EXTRACT_HTML, {"selector": "#wrapper"})
        result = self.executor._handle_extract_html(step)

        self.executor.page.inner_html.assert_called_once_with("#wrapper")
        assert result.success is True
        assert result.data == {"html": "<p>content</p>"}

    def test_extract_html_playwright_error_returns_failure(self):
        self.executor.page.inner_html.side_effect = Exception("Element detached")
        step = Step(ActionType.EXTRACT_HTML, {"selector": "#missing"})
        result = self.executor._handle_extract_html(step)

        assert result.success is False
        assert "Element detached" in result.error

    # --- SCREENSHOT ---

    def test_screenshot_calls_page_screenshot_with_path(self):
        step = Step(ActionType.SCREENSHOT, {"path": "/tmp/test.png"})
        result = self.executor._handle_screenshot(step)

        self.executor.page.screenshot.assert_called_once_with(path="/tmp/test.png")
        assert result.success is True
        assert result.data == {"path": "/tmp/test.png"}

    def test_screenshot_playwright_error_returns_failure(self):
        self.executor.page.screenshot.side_effect = Exception("Permission denied")
        step = Step(ActionType.SCREENSHOT, {"path": "/no-write/test.png"})
        result = self.executor._handle_screenshot(step)

        assert result.success is False
        assert "Permission denied" in result.error


class TestPlaywrightExecutorValidation:
    """Tests for _validate_step."""

    def setup_method(self):
        self.executor = PlaywrightExecutor()

    @pytest.mark.parametrize("action, params", [
        (ActionType.GOTO,         {"url": "https://example.com"}),
        (ActionType.FILL,         {"selector": "#el", "value": "text"}),
        (ActionType.CLICK,        {"selector": "#btn"}),
        (ActionType.SELECT,       {"selector": "#sel", "value": "opt"}),
        (ActionType.WAIT_FOR,     {"selector": "#el"}),
        (ActionType.EXTRACT_TEXT, {"selector": "#el"}),
        (ActionType.EXTRACT_HTML, {"selector": "#el"}),
        (ActionType.SCREENSHOT,   {"path": "/tmp/sc.png"}),
        (ActionType.PRESS_KEY,    {"selector": "#el", "key": "Enter"}),
    ])
    def test_validate_step_passes_when_all_params_present(self, action, params):
        step = Step(action, params)
        self.executor._validate_step(step)  # must not raise

    @pytest.mark.parametrize("action, params, missing_param", [
        (ActionType.GOTO,         {},                    "url"),
        (ActionType.FILL,         {"selector": "#el"},   "value"),
        (ActionType.FILL,         {"value": "text"},     "selector"),
        (ActionType.CLICK,        {},                    "selector"),
        (ActionType.SELECT,       {"selector": "#sel"},  "value"),
        (ActionType.WAIT_FOR,     {},                    "selector"),
        (ActionType.EXTRACT_TEXT, {},                    "selector"),
        (ActionType.EXTRACT_HTML, {},                    "selector"),
        (ActionType.SCREENSHOT,   {},                    "path"),
        (ActionType.PRESS_KEY,    {"key": "Enter"},      "selector"),
        (ActionType.PRESS_KEY,    {"selector": "#el"},   "key"),
    ])
    def test_validate_step_raises_when_param_is_missing(self, action, params, missing_param):
        step = Step(action, params)
        with pytest.raises(ValueError, match=missing_param):
            self.executor._validate_step(step)


class TestPlaywrightExecutorExecuteWorkflow:
    """Tests for execute_workflow."""

    def setup_method(self):
        self.executor = PlaywrightExecutor()
        self.executor.page = MagicMock()

    def test_returns_one_result_per_step(self):
        workflow = Workflow(
            name="test",
            steps=[
                Step(ActionType.GOTO, {"url": "https://example.com"}),
                Step(ActionType.CLICK, {"selector": "#btn"}),
            ]
        )
        results = self.executor.execute_workflow(workflow)

        assert len(results) == 2

    def test_all_successful_steps_return_success(self):
        workflow = Workflow(
            name="test",
            steps=[
                Step(ActionType.GOTO, {"url": "https://example.com"}),
                Step(ActionType.CLICK, {"selector": "#btn"}),
            ]
        )
        results = self.executor.execute_workflow(workflow)

        assert all(r.success for r in results)

    def test_continues_after_a_failed_step(self):
        self.executor.page.goto.side_effect = Exception("Network error")
        workflow = Workflow(
            name="test",
            steps=[
                Step(ActionType.GOTO, {"url": "https://example.com"}),
                Step(ActionType.CLICK, {"selector": "#btn"}),
            ]
        )
        results = self.executor.execute_workflow(workflow)

        assert results[0].success is False
        assert results[1].success is True

    def test_missing_param_step_returns_failure_and_continues(self):
        workflow = Workflow(
            name="test",
            steps=[
                Step(ActionType.GOTO, {}),  # missing url
                Step(ActionType.CLICK, {"selector": "#btn"}),
            ]
        )
        results = self.executor.execute_workflow(workflow)

        assert results[0].success is False
        assert "url" in results[0].error
        assert results[1].success is True

    def test_unknown_action_returns_failure(self):
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.GOTO, {"url": "https://example.com"})]
        )
        self.executor.actions.pop(ActionType.GOTO)

        results = self.executor.execute_workflow(workflow)

        assert results[0].success is False
        assert "Unknown action" in results[0].error


class TestPlaywrightExecutorClose:
    def test_close_with_no_resources_does_not_raise(self):
        executor = PlaywrightExecutor()
        # All resources (page, context, browser, playwright) are None by default
        executor.close()  # must not raise
