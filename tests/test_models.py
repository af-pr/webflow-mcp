"""
Unit tests for models module
"""

import pytest
from src.models import ActionType, Step, StepResult, ValidationError, Workflow


class TestActionType:
    @pytest.mark.parametrize("value, expected", [
        ("goto", ActionType.GOTO),
        ("fill", ActionType.FILL),
        ("click", ActionType.CLICK),
        ("select", ActionType.SELECT),
        ("wait_for", ActionType.WAIT_FOR),
        ("extract_text", ActionType.EXTRACT_TEXT),
        ("extract_html", ActionType.EXTRACT_HTML),
        ("screenshot", ActionType.SCREENSHOT),
    ])
    def test_from_string_value(self, value, expected):
        assert ActionType(value) == expected

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            ActionType("invalid_action")


class TestStep:
    @pytest.mark.parametrize("data, expected_action, expected_params", [
        (
            {"action": "goto", "url": "https://example.com"},
            ActionType.GOTO,
            {"url": "https://example.com"},
        ),
        (
            {"action": "fill", "selector": "#input", "value": "test value"},
            ActionType.FILL,
            {"selector": "#input", "value": "test value"},
        ),
    ])
    def test_from_dict(self, data, expected_action, expected_params):
        step = Step.from_dict(data)
        assert step.action == expected_action
        assert step.params == expected_params

    def test_from_dict_missing_action_raises(self):
        with pytest.raises(ValueError, match="must have an 'action'"):
            Step.from_dict({"selector": "#input"})

    def test_from_dict_invalid_action_raises(self):
        with pytest.raises(ValueError, match="Unknown action"):
            Step.from_dict({"action": "invalid_action"})

    @pytest.mark.parametrize("action, params", [
        (ActionType.GOTO,         {"url": "https://example.com"}),
        (ActionType.FILL,         {"selector": "#input", "value": "text"}),
        (ActionType.CLICK,        {"selector": "#btn"}),
        (ActionType.SELECT,       {"selector": "#sel", "value": "opt"}),
        (ActionType.WAIT_FOR,     {"selector": "#el"}),
        (ActionType.EXTRACT_TEXT, {"selector": "#el"}),
        (ActionType.EXTRACT_HTML, {"selector": "#el"}),
        (ActionType.SCREENSHOT,   {"path": "/tmp/sc.png"}),
        (ActionType.PRESS_KEY,    {"selector": "#el", "key": "Enter"}),
    ])
    def test_validate_passes_with_required_params(self, action, params):
        Step(action, params).validate()

    def test_validate_raises_when_param_missing(self):
        with pytest.raises(ValueError, match="missing required parameter: 'url'"):
            Step(ActionType.GOTO, {}).validate()

    def test_validate_raises_for_fill_missing_value(self):
        with pytest.raises(ValueError, match="missing required parameter: 'value'"):
            Step(ActionType.FILL, {"selector": "#input"}).validate()

    def test_required_params_covers_all_action_types(self):
        for action in ActionType:
            assert action in Step.REQUIRED_PARAMS


class TestStepResult:
    @pytest.mark.parametrize("kwargs, expected_dict", [
        (
            {"success": True, "data": {"text": "result"}},
            {"success": True, "data": {"text": "result"}, "error": None},
        ),
        (
            {"success": False, "error": "Timeout"},
            {"success": False, "data": None, "error": "Timeout"},
        ),
    ])
    def test_to_dict(self, kwargs, expected_dict):
        assert StepResult(**kwargs).to_dict() == expected_dict


class TestWorkflow:
    def test_from_dict_creates_workflow(self):
        data = {
            "name": "test_workflow",
            "steps": [{"action": "goto", "url": "https://example.com"}],
        }
        workflow = Workflow.from_dict(data)

        assert workflow.name == "test_workflow"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].action == ActionType.GOTO

    def test_from_dict_with_optional_output(self):
        data = {
            "name": "test",
            "steps": [{"action": "goto", "url": "https://example.com"}],
            "output": {"type": "file", "path": "./out.txt"},
        }
        assert Workflow.from_dict(data).output == {"type": "file", "path": "./out.txt"}

    @pytest.mark.parametrize("data, match", [
        ({"steps": [{"action": "goto", "url": "https://example.com"}]}, "name"),
        ({"name": "test"}, "steps"),
        ({"name": "test", "steps": "not a list"}, "list"),
    ])
    def test_from_dict_raises_on_invalid_structure(self, data, match):
        with pytest.raises(ValueError, match=match):
            Workflow.from_dict(data)

    def test_validate_passes_with_valid_workflow(self):
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.GOTO, {"url": "https://example.com"})]
        )
        workflow.validate()  # Should not raise

    def test_validate_raises_when_name_is_empty(self):
        workflow = Workflow(
            name="",
            steps=[Step(ActionType.GOTO, {"url": "https://example.com"})]
        )
        with pytest.raises(ValidationError, match="must have a name"):
            workflow.validate()

    def test_validate_raises_when_steps_is_empty(self):
        workflow = Workflow(name="test", steps=[])
        with pytest.raises(ValidationError, match="at least one step"):
            workflow.validate()

    def test_validate_raises_when_step_is_invalid(self):
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.GOTO, {})]  # Missing required 'url'
        )
        with pytest.raises(ValidationError, match="missing required parameter"):
            workflow.validate()
