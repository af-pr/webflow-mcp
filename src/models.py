"""
Data models for webflow-mcp

This module contains the core data classes used throughout the application.
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict
from enum import Enum

class ValidationError(ValueError):
    """Custom exception for validation errors"""
    pass


class ActionType(Enum):
    """Supported workflow action types"""
    GOTO = "goto"
    FILL = "fill"
    CLICK = "click"
    SELECT = "select"
    WAIT_FOR = "wait_for"
    WAIT_FOR_HIDDEN = "wait_for_hidden"
    WAIT_FOR_LOAD_STATE = "wait_for_load_state"
    WAIT_FOR_RESPONSE = "wait_for_response"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_INNER_TEXT = "extract_inner_text"
    EXTRACT_HTML = "extract_html"
    EXTRACT_ATTRIBUTE_VALUE = "extract_attribute_value"  # Extrae el valor de un atributo (por ejemplo, value de un input)
    SCREENSHOT = "screenshot"
    PRESS_KEY = "press_key"


@dataclass
class Step:
    """Represents a single workflow step"""
    
    # Required parameters for each action type
    REQUIRED_PARAMS = {
        ActionType.GOTO: ["url"],
        ActionType.FILL: ["selector", "value"],
        ActionType.CLICK: ["selector"],
        ActionType.SELECT: ["selector", "value"],
        ActionType.WAIT_FOR: ["selector"],
        ActionType.WAIT_FOR_HIDDEN: ["selector"],
        ActionType.WAIT_FOR_LOAD_STATE: ["state"],
        ActionType.WAIT_FOR_RESPONSE: ["url_pattern"],
        ActionType.EXTRACT_TEXT: ["selector"],
        ActionType.EXTRACT_INNER_TEXT: ["selector"],
        ActionType.EXTRACT_HTML: ["selector"],
        ActionType.EXTRACT_ATTRIBUTE_VALUE: ["selector", "attribute"],
        ActionType.SCREENSHOT: ["path"],
        ActionType.PRESS_KEY: ["selector", "key"],
    }
    
    action: ActionType
    params: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        """Create a Step from a dictionary
        
        Args:
            data: Dictionary with 'action' key and parameter keys
        
        Returns:
            Step instance
        
        Raises:
            ValidationError: If 'action' field is missing or unknown
        """
        action_str = data.get("action")
        if not action_str:
            raise ValidationError("Step must have an 'action' field")
        
        # Validate action exists
        try:
            action = ActionType(action_str)
        except ValueError:
            available = ", ".join([a.value for a in ActionType])
            raise ValidationError(
                f"Unknown action: '{action_str}'. Available actions: {available}"
            )
        
        # All keys except 'action' are parameters
        params = {k: v for k, v in data.items() if k != "action"}
        return cls(action=action, params=params)
    
    def validate(self) -> None:
        """Validate that all required parameters are present
        
        Raises:
            ValidationError: If required parameters are missing
        """
        required = self.REQUIRED_PARAMS.get(self.action, [])
        
        for param in required:
            if param not in self.params:
                raise ValidationError(
                    f"Step '{self.action.value}' missing required parameter: '{param}'"
                )


@dataclass
class StepResult:
    """Represents the result of a step execution"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary
        
        Returns:
            Dictionary representation of the result
        """
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }


@dataclass
class Workflow:
    """Represents a complete workflow"""
    name: str
    steps: list[Step]
    output: Optional[Dict[str, Any]] = None
    auth: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create a Workflow from a dictionary
        
        Args:
            data: Dictionary with 'name', 'steps', and optional 'output'/'auth' keys
        
        Returns:
            Workflow instance
        
        Raises:
            ValidationError: If required fields are missing
        """
        name = data.get("name")
        if not name:
            raise ValidationError("Workflow must have a 'name' field")
        
        steps_data = data.get("steps")
        if not steps_data:
            raise ValidationError("Workflow must have a 'steps' field")
        
        if not isinstance(steps_data, list):
            raise ValidationError("'steps' must be a list")
        
        # Convert each step dict to Step object
        steps = [Step.from_dict(step_dict) for step_dict in steps_data]
        
        output = data.get("output")
        auth = data.get("auth")
        
        return cls(name=name, steps=steps, output=output, auth=auth)

    def validate(self) -> None:
        """ Validate the workflow structure and steps
        Raises:
            ValidationError: If any step is invalid
        """
        if not self.name:
            raise ValidationError("Workflow must have a name")
        if not self.steps:
            raise ValidationError("Workflow must have at least one step")
        for step in self.steps:
            step.validate()
