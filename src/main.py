"""
webflow-mcp: Main entry point for the MCP Server

Exposes a single MCP tool `run_workflow` that:
1. Loads a YAML workflow by name
2. Resolves placeholders with the provided params
3. Executes the workflow in a real browser via Playwright
4. Returns the collected results as text
"""



import logging
import sys
import argparse
from typing import Any
import os
from dotenv import load_dotenv

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
    logger = logging.getLogger(__name__)
    logger.info(f"[MCP] Loading workflow '{name}'...")
    loader = WorkflowLoader()
    resolver = PlaceholderResolver()

    workflow = loader.load_workflow(name)
    logger.info(f"[MCP] Workflow '{workflow.name}' loaded successfully. Resolving placeholders...")
    resolved_workflow = resolver.resolve_workflow(workflow, params)
    logger.info(f"[MCP] Placeholders resolved. Executing workflow...")

    with PlaywrightExecutor() as executor:
        results = executor.execute_workflow(resolved_workflow)

    logger.info(f"[MCP] Workflow execution completed. Formatting results...")
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
    # If called with arguments, run as CLI
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-m'):
        parser = argparse.ArgumentParser(description="Run a workflow YAML with parameters.")
        parser.add_argument("workflow", help="Path to the workflow YAML file")
        parser.add_argument("--param", action="append", help="Placeholder values as key=value", default=[])
        parser.add_argument("--env", help="Path to .env file to load", default=None)
        args, unknown = parser.parse_known_args()

        # Load .env if provided
        if args.env:
            if not os.path.exists(args.env):
                raise FileNotFoundError(f".env file not found: {args.env}")
            load_dotenv(args.env)

        # Parse params
        params = {}
        for pair in args.param:
            if '=' not in pair:
                print(f"Invalid param: {pair}. Use key=value format.")
                sys.exit(1)
            k, v = pair.split('=', 1)
            params[k] = v

        logger = logging.getLogger("webflow-mcp.cli")
        logger.info(f"[CLI] Running workflow '{args.workflow}' with params: {params}")
        loader = WorkflowLoader()
        resolver = PlaceholderResolver()
        workflow = loader.load_workflow(args.workflow)
        resolved_workflow = resolver.resolve_workflow(workflow, params)
        with PlaywrightExecutor() as executor:
            results = executor.execute_workflow(resolved_workflow)
        print(_format_results(results))
        return

    # Otherwise, run as MCP server
    mcp.run()


if __name__ == "__main__":
    main()
