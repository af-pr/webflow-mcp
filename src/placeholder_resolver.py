"""
Placeholder resolver for workflow steps

This module provides the PlaceholderResolver class to resolve dynamic placeholders in workflow
steps by substituting them with actual runtime data.
"""

import logging
import re
from typing import List, Dict, Any

from src.models import Step, Workflow


class PlaceholderResolver:
    """Resolve placeholders in workflow steps"""
    
    def __init__(self):
        """Initialize PlaceholderResolver"""
        self.logger = logging.getLogger(__name__)
    
    def resolve_workflow(self, workflow: Workflow, data: Dict[str, Any]) -> Workflow:
        """
        Resolve placeholders in a workflow
        
        Creates a new Workflow with all {{placeholder}} tokens in the steps
        substituted with values from the provided data dictionary.
        
        Args:
            workflow: Workflow object potentially containing placeholders
            data: Dictionary mapping placeholder names to their values
        
        Returns:
            New Workflow object with all placeholders resolved
        
        Raises:
            ValidationError: If unresolved placeholders remain after substitution
        """
        resolved_steps = self._resolve_steps_internal(workflow.steps, data)
        return Workflow(name=workflow.name, steps=resolved_steps, output=workflow.output)
    
    def _resolve_steps_internal(self, steps: List[Step], data: Dict[str, Any]) -> List[Step]:
        """
        Internal method to resolve placeholders in a list of steps.
        
        Args:
            steps: List of Step objects potentially containing placeholders
            data: Dictionary mapping placeholder names to their values
        
        Returns:
            List of Step objects with all placeholders resolved
        """
        resolved_steps = []
        
        for step in steps:
            resolved_params = self._resolve_params(step.params, data)
            resolved_step = Step(action=step.action, params=resolved_params)
            resolved_steps.append(resolved_step)
        
        self._validate_no_unresolved(resolved_steps)
        return resolved_steps
    
    @staticmethod
    def _resolve_params(
        params: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve placeholders in a parameters dictionary
        
        Args:
            params: Parameters dictionary potentially containing placeholders
            data: Dictionary with values to substitute
        
        Returns:
            Dictionary with all placeholders resolved
        """
        result = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                # Replace {{placeholder}} with values from data
                for data_key, data_value in data.items():
                    placeholder = f"{{{{{data_key}}}}}"
                    if placeholder in value:
                        value = value.replace(placeholder, str(data_value))
            
            result[key] = value
        
        return result

    @staticmethod
    def _validate_no_unresolved(steps: List[Step]) -> None:
        """
        Validates that there are no unresolved {{placeholder}} tokens in the provided steps.

        Args:
            steps: List of Step objects after resolution

        Raises:
            ValidationError: If unresolved placeholders are found
        """
        from src.models import ValidationError

        pattern = re.compile(r"\{\{(\w+)\}\}")
        unresolved = set()

        for step in steps:
            for value in step.params.values():
                if isinstance(value, str):
                    unresolved.update(pattern.findall(value))

        if unresolved:
            missing = ", ".join(sorted(unresolved))
            raise ValidationError(f"Unresolved placeholders: {missing}")
