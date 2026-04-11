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

    def test_custom_config(self):
        executor = PlaywrightExecutor(headless=False, timeout=5000)
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

    # --- EXTRACT_ATTRIBUTE_VALUE ---
    def test_extract_attribute_value_calls_page_get_attribute_and_returns_value(self):
        self.executor.page.get_attribute.return_value = "myval"
        step = Step(ActionType.EXTRACT_ATTRIBUTE_VALUE, {"selector": "#input", "attribute": "value"})
        result = self.executor._handle_extract_attribute_value(step)
        self.executor.page.get_attribute.assert_called_once_with("#input", "value")
        assert result.success is True
        assert result.data == {"value": "myval"}

    def test_extract_attribute_value_playwright_error_returns_failure(self):
        self.executor.page.get_attribute.side_effect = Exception("Element not found")
        step = Step(ActionType.EXTRACT_ATTRIBUTE_VALUE, {"selector": "#input", "attribute": "value"})
        result = self.executor._handle_extract_attribute_value(step)
        assert result.success is False
        assert "Element not found" in result.error

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

    # --- WAIT_FOR_HIDDEN ---

    def test_wait_for_hidden_calls_wait_for_selector_with_hidden_state(self):
        # Arrange
        step = Step(ActionType.WAIT_FOR_HIDDEN, {"selector": ".loading-spinner"})

        # Act
        result = self.executor._handle_wait_for_hidden(step)

        # Assert
        self.executor.page.wait_for_selector.assert_called_once_with(".loading-spinner", state="hidden")
        assert result.success is True
        assert result.data == {"selector": ".loading-spinner"}

    def test_wait_for_hidden_timeout_returns_failure(self):
        # Arrange
        self.executor.page.wait_for_selector.side_effect = Exception("Timeout waiting for hidden")
        step = Step(ActionType.WAIT_FOR_HIDDEN, {"selector": ".never-hides"})

        # Act
        result = self.executor._handle_wait_for_hidden(step)

        # Assert
        assert result.success is False
        assert "Timeout waiting for hidden" in result.error

    # --- WAIT_FOR_LOAD_STATE ---

    def test_wait_for_load_state_calls_page_wait_for_load_state(self):
        # Arrange
        step = Step(ActionType.WAIT_FOR_LOAD_STATE, {"state": "networkidle"})

        # Act
        result = self.executor._handle_wait_for_load_state(step)

        # Assert
        self.executor.page.wait_for_load_state.assert_called_once_with("networkidle")
        assert result.success is True
        assert result.data == {"state": "networkidle"}

    def test_wait_for_load_state_with_different_states(self):
        # Test that different states pass through correctly
        for state in ["load", "domcontentloaded", "networkidle"]:
            self.executor.page.wait_for_load_state.reset_mock()
            step = Step(ActionType.WAIT_FOR_LOAD_STATE, {"state": state})

            result = self.executor._handle_wait_for_load_state(step)

            self.executor.page.wait_for_load_state.assert_called_once_with(state)
            assert result.success is True

    def test_wait_for_load_state_timeout_returns_failure(self):
        # Arrange
        self.executor.page.wait_for_load_state.side_effect = Exception("Timeout 30000ms exceeded")
        step = Step(ActionType.WAIT_FOR_LOAD_STATE, {"state": "networkidle"})

        # Act
        result = self.executor._handle_wait_for_load_state(step)

        # Assert
        assert result.success is False
        assert "Timeout 30000ms exceeded" in result.error

    # --- WAIT_FOR_RESPONSE ---

    def test_wait_for_response_calls_page_wait_for_response(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.url = "https://api.example.com/generate"
        self.executor.page.wait_for_response.return_value = mock_response
        step = Step(ActionType.WAIT_FOR_RESPONSE, {"url_pattern": "**/api/generate**"})

        # Act
        result = self.executor._handle_wait_for_response(step)

        # Assert
        # wait_for_response gets called with (pattern, timeout=30000) as default
        self.executor.page.wait_for_response.assert_called_once_with("**/api/generate**", timeout=30000)
        assert result.success is True
        assert result.data["url_pattern"] == "**/api/generate**"
        assert result.data["status"] == 200
        assert result.data["url"] == "https://api.example.com/generate"

    def test_wait_for_response_with_custom_timeout(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.url = "https://api.example.com/slow-endpoint"
        self.executor.page.wait_for_response.return_value = mock_response
        step = Step(ActionType.WAIT_FOR_RESPONSE, {
            "url_pattern": "**/slow-endpoint**",
            "timeout": 60000
        })

        # Act
        result = self.executor._handle_wait_for_response(step)

        # Assert
        self.executor.page.wait_for_response.assert_called_once_with("**/slow-endpoint**", timeout=60000)
        assert result.success is True

    def test_wait_for_response_timeout_returns_failure(self):
        # Arrange
        self.executor.page.wait_for_response.side_effect = Exception("Timeout waiting for response")
        step = Step(ActionType.WAIT_FOR_RESPONSE, {"url_pattern": "**/never-comes**"})

        # Act
        result = self.executor._handle_wait_for_response(step)

        # Assert
        assert result.success is False
        assert "Timeout waiting for response" in result.error

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

    # --- EXTRACT_INNER_TEXT ---

    def test_extract_inner_text_calls_page_inner_text_and_returns_text(self):
        # Arrange
        self.executor.page.inner_text.return_value = "Line 1\nLine 2\n- item"
        step = Step(ActionType.EXTRACT_INNER_TEXT, {"selector": ".response"})

        # Act
        result = self.executor._handle_extract_inner_text(step)

        # Assert
        self.executor.page.inner_text.assert_called_once_with(".response")
        assert result.success is True
        assert result.data == {"text": "Line 1\nLine 2\n- item"}

    def test_extract_inner_text_preserves_newlines_from_block_elements(self):
        # inner_text() returns newlines for block-level elements — verify we don't strip them
        # Arrange
        self.executor.page.inner_text.return_value = "Paragraph 1\n\nParagraph 2"
        step = Step(ActionType.EXTRACT_INNER_TEXT, {"selector": "#content"})

        # Act
        result = self.executor._handle_extract_inner_text(step)

        # Assert
        assert result.data["text"] == "Paragraph 1\n\nParagraph 2"

    def test_extract_inner_text_playwright_error_returns_failure(self):
        # Arrange
        self.executor.page.inner_text.side_effect = Exception("Selector not found")
        step = Step(ActionType.EXTRACT_INNER_TEXT, {"selector": "#missing"})

        # Act
        result = self.executor._handle_extract_inner_text(step)

        # Assert
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
        (ActionType.WAIT_FOR,              {"selector": "#el"}),
        (ActionType.WAIT_FOR_HIDDEN,        {"selector": "#el"}),
        (ActionType.WAIT_FOR_LOAD_STATE,    {"state": "networkidle"}),
        (ActionType.WAIT_FOR_RESPONSE,      {"url_pattern": "**/api/**"}),
        (ActionType.EXTRACT_TEXT,           {"selector": "#el"}),
        (ActionType.EXTRACT_INNER_TEXT,  {"selector": "#el"}),
        (ActionType.EXTRACT_HTML,        {"selector": "#el"}),
        (ActionType.SCREENSHOT,   {"path": "/tmp/sc.png"}),
        (ActionType.PRESS_KEY,    {"selector": "#el", "key": "Enter"}),
        (ActionType.EXTRACT_ATTRIBUTE_VALUE, {"selector": "#input", "attribute": "value"}),
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
        (ActionType.WAIT_FOR,              {},  "selector"),
        (ActionType.WAIT_FOR_HIDDEN,        {},  "selector"),
        (ActionType.WAIT_FOR_LOAD_STATE,    {},  "state"),
        (ActionType.WAIT_FOR_RESPONSE,      {},  "url_pattern"),
        (ActionType.EXTRACT_TEXT,           {},  "selector"),
        (ActionType.EXTRACT_INNER_TEXT,  {},  "selector"),
        (ActionType.EXTRACT_HTML,        {},  "selector"),
        (ActionType.SCREENSHOT,   {},                    "path"),
        (ActionType.PRESS_KEY,    {"key": "Enter"},      "selector"),
        (ActionType.PRESS_KEY,    {"selector": "#el"},   "key"),
        (ActionType.EXTRACT_ATTRIBUTE_VALUE, {"selector": "#input"}, "attribute"),
        (ActionType.EXTRACT_ATTRIBUTE_VALUE, {"attribute": "value"}, "selector"),
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
        # Mock browser so _create_context doesn't require a real browser
        mock_context = MagicMock()
        mock_context.new_page.return_value = self.executor.page
        self.executor.browser = MagicMock()
        self.executor.browser.new_context.return_value = mock_context

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
        executor.close()  # must not raise


class TestPlaywrightExecutorAuth:
    """Tests for _create_context auth loading logic."""

    def _make_executor_with_mock_browser(self):
        executor = PlaywrightExecutor()
        mock_context = MagicMock()
        mock_context.new_page.return_value = MagicMock()
        executor.browser = MagicMock()
        executor.browser.new_context.return_value = mock_context
        return executor

    def _make_workflow(self, auth=None):
        return Workflow(
            name="test",
            steps=[Step(ActionType.GOTO, {"url": "https://example.com"})],
            auth=auth,
        )

    def test_no_auth_creates_context_without_storage_state(self):
        executor = self._make_executor_with_mock_browser()
        
        executor._create_context(self._make_workflow(auth=None))
        
        executor.browser.new_context.assert_called_once_with()

    def test_auth_loads_storage_state(self, tmp_path):
        executor = self._make_executor_with_mock_browser()
        auth_file = tmp_path / "mysite.json"
        auth_file.write_text('{"cookies": [], "origins": []}')
        import src.playwright_executor as mod
        original = mod.AUTH_DIR
        mod.AUTH_DIR = tmp_path
        
        try:
            executor._create_context(self._make_workflow(auth="mysite"))
            
            executor.browser.new_context.assert_called_once_with(
                storage_state=str(auth_file)
            )
        finally:
            mod.AUTH_DIR = original

    def test_auth_raises_file_not_found_when_missing(self):
        executor = self._make_executor_with_mock_browser()
        
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            executor._create_context(self._make_workflow(auth="nonexistent"))

    def test_auth_error_message_includes_save_auth_hint(self):
        executor = self._make_executor_with_mock_browser()
        
        with pytest.raises(FileNotFoundError, match="save_auth.py"):
            executor._create_context(self._make_workflow(auth="nonexistent"))

    def test_execute_workflow_raises_file_not_found_for_missing_auth(self):
        executor = self._make_executor_with_mock_browser()
        workflow = self._make_workflow(auth="missing")
        
        with pytest.raises(FileNotFoundError):
            executor.execute_workflow(workflow)
