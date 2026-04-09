"""
Placeholder resolver for workflow steps

This module provides the PlaceholderResolver class to resolve dynamic placeholders in workflow
steps by substituting them with actual runtime data.
"""

import logging
from typing import List, Dict, Any

from src.models import Step


class PlaceholderResolver:
    """Resolve placeholders in workflow steps"""
    
    def __init__(self):
        """Initialize PlaceholderResolver"""
        self.logger = logging.getLogger(__name__)
    
    def resolve_steps(
        self,
        steps: List[Step],
        data: Dict[str, Any]
    ) -> List[Step]:
        """
        Resolve placeholders in all steps
        
        Substitutes all occurrences of {{placeholder}} in step parameters
        with corresponding values from the data dictionary.
        
        Args:
            steps: List of Step objects potentially containing placeholders
            data: Dictionary mapping placeholder names to their values
        
        Returns:
            List of Step objects with all placeholders resolved
        
        Example:
            steps = [
                Step(ActionType.GOTO, {"url": "https://example.com"}),
                Step(ActionType.FILL, {"selector": "#input", "value": "{{question}}"})
            ]
            data = {"question": "What is AI?"}
            
            resolved = resolver.resolve_steps(steps, data)
            # resolved[1].params["value"] == "What is AI?"
        """
        resolved_steps = []
        
        for step in steps:
            resolved_params = self._resolve_params(step.params, data)
            resolved_step = Step(action=step.action, params=resolved_params)
            resolved_steps.append(resolved_step)
        
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
