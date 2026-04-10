"""
webflow-mcp: Main entry point for the MCP Server

Exposes a single MCP tool `run_workflow` that:
1. Loads a YAML workflow by name
2. Resolves placeholders with the provided params
3. Executes the workflow in a real browser via Playwright
4. Returns the collected results as text
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.workflow_loader import WorkflowLoader
from src.placeholder_resolver import PlaceholderResolver
from src.playwright_executor import PlaywrightExecutor

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("webflow-mcp")


@mcp.tool()
def run_workflow(name: str, params: dict[str, Any]) -> str:
    """
    Load and execute the provided workflow.

    Args:
        name: Name of the workflow file (with or without .yaml extension)
        params: Dictionary of placeholder values to substitute in the workflow steps

    Returns:
        A text summary of each step result
    """
    loader = WorkflowLoader()
    resolver = PlaceholderResolver()

    workflow = loader.load_workflow(name)
    resolved_workflow = resolver.resolve_workflow(workflow, params)

    with PlaywrightExecutor() as executor:
        results = executor.execute_workflow(resolved_workflow)

    return _format_results(results)


def _format_results(results: list) -> str:
    lines = []
    for idx, result in enumerate(results, start=1):
        if result.success:
            data_str = str(result.data) if result.data is not None else "ok"
            lines.append(f"Step {idx}: OK — {data_str}")
        else:
            lines.append(f"Step {idx}: FAILED — {result.error}")
    return "\n".join(lines)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
