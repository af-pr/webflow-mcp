"""
Workflow loader and parser

This module provides the WorkflowLoader class to load and parse workflow YAML files
into Workflow objects.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Union

import yaml

from src.models import Workflow

WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"

class WorkflowLoader:
    """Load and parse workflow YAML files"""
    
    def __init__(self, workflows_dir: Union[str, Path] = WORKFLOWS_DIR) -> None:
        """
        Initialize WorkflowLoader
        
        Args:
            workflows_dir: Directory path containing workflow YAML files
        """
        self.workflows_dir = Path(workflows_dir)
        self.logger = logging.getLogger(__name__)
    
    def load_workflow(self, name: str) -> Workflow:
        """
        Load a workflow from a file in the templates directory with the provided name
        
        Args:
            name: Name of the workflow. It might be a simple name or with the .yaml extension. Examples: "test_workflow" or "test_workflow.yaml"
        
        Returns:
            Workflow object containing the name, steps, and output configuration
        
        Raises:
            FileNotFoundError: If the workflow YAML file does not exist
            yaml.YAMLError: If the YAML is malformed
            ValidationError: If the workflow structure is invalid
        """
        file_path = self._resolve_workflow_path(name)
        data = self._load_yaml(file_path)
        workflow = Workflow.from_dict(data)
        workflow.validate()
        return workflow

    def _resolve_workflow_path(self, workflow_name: str) -> Path:
        """
        Returns the full path to the workflow YAML file in the templates directory
        
        Args:
            workflow_name: Name of the workflow file, with or without .yaml extension
        """
        if not workflow_name.endswith(".yaml"):
            workflow_name += ".yaml"
        return self.workflows_dir / workflow_name
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """
        Load and parse a YAML file in the provided file path
        
        Args:
            file_path: Full path to the YAML file
        
        Raises:
            FileNotFoundError: If the file does not exist
            yaml.YAMLError: If the YAML is malformed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")
        
        with open(file_path, "r") as f:
            try:
                data = yaml.safe_load(f)
                return data
            except yaml.YAMLError as e:
                self.logger.error(f"Error parsing YAML file {file_path}: {e}")
                raise
