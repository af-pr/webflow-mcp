"""
Unit tests for the main MCP server module
"""

import pytest
from unittest.mock import MagicMock, patch

from src.main import _format_results, run_workflow
from src.models import StepResult, ActionType, Step, Workflow, ValidationError


class TestFormatResults:
    """Tests for the _format_results formatting function"""

    def test_format_single_successful_result(self):
        results = [StepResult(success=True, data={"url": "https://example.com"})]
        output = _format_results(results)
        
        assert "Step 1: OK" in output
        assert "https://example.com" in output

    def test_format_single_failed_result(self):
        results = [StepResult(success=False, error="Network error")]
        output = _format_results(results)
        
        assert "Step 1: FAILED" in output
        assert "Network error" in output

    def test_format_successful_result_without_data(self):
        results = [StepResult(success=True)]
        output = _format_results(results)
        
        assert "Step 1: OK — ok" in output

    def test_format_multiple_results(self):
        results = [
            StepResult(success=True, data={"step": 1}),
            StepResult(success=False, error="Timeout"),
            StepResult(success=True, data={"step": 3}),
        ]
        output = _format_results(results)
        lines = output.split("\n")
        
        assert len(lines) == 3
        assert "Step 1: OK" in lines[0]
        assert "Step 2: FAILED" in lines[1]
        assert "Step 3: OK" in lines[2]

    def test_format_all_successful_results(self):
        results = [
            StepResult(success=True, data={"page": "loaded"}),
            StepResult(success=True, data={"text": "extracted"}),
            StepResult(success=True, data={"screenshot": "saved"}),
        ]
        output = _format_results(results)
        
        assert "FAILED" not in output
        assert output.count("OK") == 3

    def test_format_all_failed_results(self):
        results = [
            StepResult(success=False, error="Error 1"),
            StepResult(success=False, error="Error 2"),
            StepResult(success=False, error="Error 3"),
        ]
        output = _format_results(results)
        
        assert "OK" not in output
        assert output.count("FAILED") == 3


class TestRunWorkflow:
    """Tests for the run_workflow MCP tool"""

    @patch("src.main.PlaywrightExecutor")
    @patch("src.main.PlaceholderResolver")
    @patch("src.main.WorkflowLoader")
    def test_run_workflow_happy_path(self, mock_loader_cls, mock_resolver_cls, mock_executor_cls):
        # Setup mocks
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.GOTO, {"url": "https://example.com"})]
        )
        resolved_workflow = Workflow(
            name="test",
            steps=[Step(ActionType.GOTO, {"url": "https://example.com"})]
        )
        results = [StepResult(success=True, data={"url": "https://example.com"})]

        mock_loader = MagicMock()
        mock_loader.load_workflow.return_value = workflow
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver.resolve_workflow.return_value = resolved_workflow
        mock_resolver_cls.return_value = mock_resolver

        mock_executor = MagicMock()
        mock_executor.execute_workflow.return_value = results
        mock_executor_cls.return_value.__enter__.return_value = mock_executor

        # Execute
        output = run_workflow("test_workflow", {})

        # Verify
        assert "Step 1: OK" in output
        assert "https://example.com" in output
        mock_loader.load_workflow.assert_called_once_with("test_workflow")
        mock_resolver.resolve_workflow.assert_called_once_with(workflow, {})
        mock_executor.execute_workflow.assert_called_once_with(resolved_workflow)

    @patch("src.main.WorkflowLoader")
    def test_run_workflow_with_params(self, mock_loader_cls):
        # Setup: WorkflowLoader fails, but we're testing param passing
        mock_loader = MagicMock()
        mock_loader.load_workflow.side_effect = FileNotFoundError("Workflow not found")
        mock_loader_cls.return_value = mock_loader

        # Execute and verify error is propagated
        with pytest.raises(FileNotFoundError):
            run_workflow("nonexistent", {"param1": "value1", "param2": "value2"})

        mock_loader.load_workflow.assert_called_once_with("nonexistent")

    @patch("src.main.PlaywrightExecutor")
    @patch("src.main.PlaceholderResolver")
    @patch("src.main.WorkflowLoader")
    def test_run_workflow_with_placeholder_resolution(self, mock_loader_cls, mock_resolver_cls, mock_executor_cls):
        # Setup workflow with placeholders
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.FILL, {"selector": "#input", "value": "{{question}}"})]
        )
        resolved_workflow = Workflow(
            name="test",
            steps=[Step(ActionType.FILL, {"selector": "#input", "value": "What is AI?"})]
        )
        results = [StepResult(success=True, data={"selector": "#input"})]

        mock_loader = MagicMock()
        mock_loader.load_workflow.return_value = workflow
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver.resolve_workflow.return_value = resolved_workflow
        mock_resolver_cls.return_value = mock_resolver

        mock_executor = MagicMock()
        mock_executor.execute_workflow.return_value = results
        mock_executor_cls.return_value.__enter__.return_value = mock_executor

        # Execute with params
        params = {"question": "What is AI?"}
        output = run_workflow("test_workflow", params)

        # Verify placeholder resolution was called with correct params
        mock_resolver.resolve_workflow.assert_called_once_with(workflow, params)
        assert "Step 1: OK" in output

    @patch("src.main.PlaywrightExecutor")
    @patch("src.main.PlaceholderResolver")
    @patch("src.main.WorkflowLoader")
    def test_run_workflow_handles_unresolved_placeholders(self, mock_loader_cls, mock_resolver_cls, mock_executor_cls):
        # Setup: resolver raises ValidationError for unresolved placeholders
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.FILL, {"value": "{{missing}}"})]
        )

        mock_loader = MagicMock()
        mock_loader.load_workflow.return_value = workflow
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver.resolve_workflow.side_effect = ValidationError("Unresolved placeholders: missing")
        mock_resolver_cls.return_value = mock_resolver

        # Execute and verify error is propagated
        with pytest.raises(ValidationError, match="missing"):
            run_workflow("test_workflow", {})

    @patch("src.main.PlaywrightExecutor")
    @patch("src.main.PlaceholderResolver")
    @patch("src.main.WorkflowLoader")
    def test_run_workflow_handles_execution_failure(self, mock_loader_cls, mock_resolver_cls, mock_executor_cls):
        # Setup: workflow execution returns failure results
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.GOTO, {"url": "https://bad.url"})]
        )
        resolved_workflow = workflow
        results = [StepResult(success=False, error="net::ERR_NAME_NOT_RESOLVED")]

        mock_loader = MagicMock()
        mock_loader.load_workflow.return_value = workflow
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver.resolve_workflow.return_value = resolved_workflow
        mock_resolver_cls.return_value = mock_resolver

        mock_executor = MagicMock()
        mock_executor.execute_workflow.return_value = results
        mock_executor_cls.return_value.__enter__.return_value = mock_executor

        # Execute
        output = run_workflow("test_workflow", {})

        # Verify failure is reported in output
        assert "Step 1: FAILED" in output
        assert "net::ERR_NAME_NOT_RESOLVED" in output

    @patch("src.main.PlaywrightExecutor")
    @patch("src.main.PlaceholderResolver")
    @patch("src.main.WorkflowLoader")
    def test_run_workflow_uses_context_manager(self, mock_loader_cls, mock_resolver_cls, mock_executor_cls):
        # Setup
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.GOTO, {"url": "https://example.com"})]
        )
        resolved_workflow = workflow
        results = [StepResult(success=True)]

        mock_loader = MagicMock()
        mock_loader.load_workflow.return_value = workflow
        mock_loader_cls.return_value = mock_loader

        mock_resolver = MagicMock()
        mock_resolver.resolve_workflow.return_value = resolved_workflow
        mock_resolver_cls.return_value = mock_resolver

        mock_executor = MagicMock()
        mock_executor.execute_workflow.return_value = results
        mock_executor_cls.return_value.__enter__.return_value = mock_executor
        mock_executor_cls.return_value.__exit__.return_value = False

        # Execute
        run_workflow("test_workflow", {})

        # Verify context manager was used (__enter__ and __exit__ called)
        mock_executor_cls.return_value.__enter__.assert_called_once()
        mock_executor_cls.return_value.__exit__.assert_called_once()
