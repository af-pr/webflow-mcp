"""
Unit tests for placeholder_resolver module
"""

import pytest
from src.models import ActionType, Step, ValidationError, Workflow
from src.placeholder_resolver import PlaceholderResolver


@pytest.fixture
def resolver():
    return PlaceholderResolver()


class TestPlaceholderResolver:
    def test_no_placeholders_leaves_params_unchanged(self, resolver):
        workflow = Workflow(
            name="test",
            steps=[
                Step(ActionType.GOTO, {"url": "https://example.com"}),
                Step(ActionType.FILL, {"selector": "#input", "value": "static text"}),
            ]
        )
        resolved = resolver.resolve_workflow(workflow, {})

        assert resolved.steps[0].params["url"] == "https://example.com"
        assert resolved.steps[1].params["value"] == "static text"

    @pytest.mark.parametrize("template, data, expected", [
        ("{{question}}", {"question": "What is AI?"}, "What is AI?"),
        ("Hello {{name}}, your ID is {{id}}", {"name": "Alice", "id": "123"}, "Hello Alice, your ID is 123"),
        ("ID: {{id}}", {"id": 12345}, "ID: 12345"),
        ("Active: {{is_active}}", {"is_active": True}, "Active: True"),
    ])
    def test_resolves_value_placeholders(self, resolver, template, data, expected):
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.FILL, {"value": template})]
        )
        resolved = resolver.resolve_workflow(workflow, data)
        assert resolved.steps[0].params["value"] == expected

    def test_missing_placeholder_key_raises_validation_error(self, resolver):
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.FILL, {"value": "{{missing_key}}"})]
        )
        with pytest.raises(ValidationError, match="missing_key"):
            resolver.resolve_workflow(workflow, {"other_key": "value"})

    def test_multiple_unresolved_placeholders_reported_together(self, resolver):
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.FILL, {"value": "{{a}} and {{b}}"})]
        )
        with pytest.raises(ValidationError, match="a"):
            resolver.resolve_workflow(workflow, {})

    def test_partially_resolved_remaining_placeholder_raises(self, resolver):
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.FILL, {"value": "{{provided}} and {{missing}}"})]
        )
        with pytest.raises(ValidationError, match="missing"):
            resolver.resolve_workflow(workflow, {"provided": "ok"})

    def test_non_string_param_values_are_not_modified(self, resolver):
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.GOTO, {"url": "https://example.com", "timeout": 5000})]
        )
        resolved = resolver.resolve_workflow(workflow, {})
        assert resolved.steps[0].params["timeout"] == 5000

    def test_resolve_workflow_does_not_mutate_original_workflow(self, resolver):
        original_value = "{{question}}"
        workflow = Workflow(
            name="test",
            steps=[Step(ActionType.FILL, {"value": original_value})]
        )
        resolver.resolve_workflow(workflow, {"question": "What is AI?"})
        assert workflow.steps[0].params["value"] == original_value

    def test_complex_workflow_resolution(self, resolver):
        workflow = Workflow(
            name="test_workflow",
            steps=[
                Step(ActionType.GOTO, {"url": "https://notebooklm.com/nb/{{notebook_id}}"}),
                Step(ActionType.FILL, {"selector": "#input", "value": "{{question}}"}),
                Step(ActionType.CLICK, {"selector": "#submit"}),
                Step(ActionType.EXTRACT_TEXT, {"selector": "#result"}),
            ]
        )
        data = {"notebook_id": "abc123", "question": "What is MCP?"}
        resolved = resolver.resolve_workflow(workflow, data)

        assert len(resolved.steps) == 4
        assert resolved.steps[0].params["url"] == "https://notebooklm.com/nb/abc123"
        assert resolved.steps[1].params["value"] == "What is MCP?"
        assert resolved.steps[2].params["selector"] == "#submit"
