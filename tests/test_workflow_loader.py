"""
Unit tests for workflow_loader module
"""

import pytest
import yaml

from src.workflow_loader import WorkflowLoader
from src.models import Workflow, ActionType, ValidationError

@pytest.fixture
def workflows_dir(tmp_path):
    dir_ = tmp_path / "workflows"
    dir_.mkdir()
    return dir_

def write_workflow_yaml(workflows_dir, workflow_name, workflow_data):
    yaml_path = workflows_dir / f"{workflow_name}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(workflow_data, file)

def test_load_valid_workflow(tmp_path):
    workflow_name = "test_workflow"
    workflow_data = {
        "name": workflow_name,
        "steps": [
            {"action": ActionType.GOTO.value , "url": "https://example.com"},
            {"action": ActionType.FILL.value , "selector": "#input", "value": "test value"},
        ],
        "output": {
            "type": "stdout"
        }
    }
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    write_workflow_yaml(workflows_dir, workflow_name, workflow_data)
    loader = WorkflowLoader(workflows_dir=str(workflows_dir))

    response = loader.load_workflow(workflow_name)

    assert isinstance(response, Workflow)
    assert response.name == workflow_name
    assert len(response.steps) == 2
    assert response.output == {"type": "stdout"}

def test_load_workflow_accepts_yaml_extension(workflows_dir):
    workflow_name = "test_workflow"
    workflow_data = {
        "name": workflow_name,
        "steps": [
            {"action": ActionType.GOTO.value, "url": "https://example.com"},
        ],
    }
    write_workflow_yaml(workflows_dir, workflow_name, workflow_data)
    loader = WorkflowLoader(workflows_dir=str(workflows_dir))

    response = loader.load_workflow("test_workflow.yaml")

    assert isinstance(response, Workflow)
    assert response.name == workflow_name


def test_load_workflow_raises_file_not_found(workflows_dir):
    loader = WorkflowLoader(workflows_dir=str(workflows_dir))

    with pytest.raises(FileNotFoundError):
        loader.load_workflow("missing_workflow")


def test_load_workflow_raises_yaml_error_for_malformed_yaml(workflows_dir):
    yaml_path = workflows_dir / "invalid_workflow.yaml"
    yaml_path.write_text("name: test\nsteps:\n  - action: goto\n    url: [", encoding="utf-8")
    loader = WorkflowLoader(workflows_dir=str(workflows_dir))

    with pytest.raises(yaml.YAMLError):
        loader.load_workflow("invalid_workflow")


def test_load_workflow_raises_validation_error_for_invalid_workflow(workflows_dir):
    workflow_name = "invalid_workflow"
    workflow_data = {
        "steps": [
            {"action": ActionType.GOTO.value, "url": "https://example.com"},
        ],
    }
    write_workflow_yaml(workflows_dir, workflow_name, workflow_data)
    loader = WorkflowLoader(workflows_dir=str(workflows_dir))

    with pytest.raises(ValidationError):
        loader.load_workflow(workflow_name)
