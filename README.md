# webflow-mcp

A generic MCP (Model Context Protocol) Server for automating web workflows using Playwright and YAML configuration files.

## Overview

webflow-mcp allows you to define, manage, and execute web automation workflows through the Model Context Protocol. Define your workflows using simple, readable YAML files—no need to write complex code for each automation task.

**Key idea:** Separate workflow definition (YAML) from execution (Python/Playwright). This makes it easy to maintain, reuse, and share automation workflows.

## Project Structure

```
webflow-mcp/
├── src/
│   ├── main.py                 # MCP Server entry point
│   ├── models.py               # Data classes (Step, Workflow, ActionType, etc.)
│   ├── placeholder_resolver.py # Template substitution ({{placeholder}})
│   ├── workflow_loader.py      # YAML workflow loading
│   └── playwright_executor.py  # Browser automation with Playwright
├── workflows/                  # Workflow YAML files
├── tests/                      # Unit and integration tests
├── output/                     # Results and logs output
├── auth/                       # Browser authentication contexts (auth.json)
├── config/                     # Configuration files
├── README.md                   # This file
├── pyproject.toml              # Project metadata and dependencies
├── requirements.txt            # Python dependencies
├── LICENSE                     # MIT License
└── .gitignore                  # Git ignore rules
```

## Architecture

### Core Components

- **models.py**: Data classes and enums
  - `ActionType`: Enum of supported workflow actions
  - `Step`: Single workflow step with action and parameters
  - `StepResult`: Result of step execution
  - `Workflow`: Complete workflow with steps and output configuration

- **placeholder_resolver.py**: Template substitution
  - `PlaceholderResolver`: Resolves `{{placeholder}}` in step parameters with runtime data

- **workflow_loader.py**: YAML workflow loading
  - `WorkflowLoader`: Loads and parses YAML workflow files into Workflow objects

- **playwright_executor.py**: Browser automation
  - `PlaywrightExecutor`: Executes workflow steps using Playwright
  - Action handlers for each supported action type
  - Context manager for safe resource cleanup

- **main.py**: MCP Server — exposes `run_workflow` tool via the Model Context Protocol

## Installation

### Option 1: Development Installation (Recommended)

Clone the repository and install in editable mode:

```bash
git clone https://github.com/af-pr/webflow-mcp
cd webflow-mcp
pip install -e .
```

### Option 2: Standard Installation

```bash
pip install -r requirements.txt
```

## Getting Started

### 1. Install Playwright Browsers

After installation, run:

```bash
playwright install chromium
```

### 2. Create Your First Workflow

Example workflow YAML file (`workflows/example.yaml`):

```yaml
name: example_workflow
steps:
  - action: goto
    url: "https://example.com"
  - action: fill
    selector: "#search"
    value: "{{search_query}}"
  - action: click
    selector: "#search-button"
  - action: wait_for
    selector: "#results"
  - action: extract_text
    selector: "#results"
output:
  type: stdout  # pending implementation — currently has no effect
```

### 3. Use with Claude (MCP)

Define your workflow YAML, then ask Claude to run it by providing:
- The workflow name
- The parameters it needs

**Example: You create `workflows/search_site.yaml`:**

```yaml
name: search_site
steps:
  - action: goto
    url: "https://example.com/search"
  - action: fill
    selector: "input[name='q']"
    value: "{{query}}"
  - action: click
    selector: "button[type='submit']"
  - action: wait_for
    selector: ".results"
  - action: extract_text
    selector: ".results .title"
```

**Then tell Claude:**

> Run my `search_site` workflow to search for "webflow automation"

Claude will call `run_workflow(name: "search_site", params: {"query": "webflow automation"})` and return the results.

## Workflow Execution Flow

1. **Define**: Write a YAML workflow file in `workflows/`
2. **Invoke**: Ask Claude to run it by name, providing the required parameters
3. **Results**: Claude returns the output of each step as formatted text

## Features

### MVP (Current)
- ✅ Load and parse workflow YAML files
- ✅ Dynamic placeholder substitution (`{{placeholder}}`)
- ✅ Placeholder validation — raises error if any remain unresolved
- ✅ MCP Server integration via FastMCP (`run_workflow` tool)
- ✅ Playwright automation execution
- ✅ Context manager for safe resource management
- ✅ Comprehensive logging
- ✅ Error handling and reporting
- ✅ Extensible action handler pattern

### Future Enhancements
- 🔄 Output file writing
- 🔄 Security measures
- 🔄 Workflow composition (nested workflows)
- 🔄 Additional action types
- 🔄 Advanced authentication options
- 🔄 CI/CD integration examples

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Code Quality

```bash
black src/
pylint src/
```

## Supported Workflow Actions

- `goto`: Navigate to a URL
- `fill`: Fill form inputs
- `click`: Click on elements
- `select`: Select dropdown options
- `wait_for`: Wait for element to appear
- `press_key`: Press a keyboard key on an element
- `extract_text`: Extract text content from elements
- `extract_html`: Extract HTML from elements
- `screenshot`: Take a screenshot

## Legal Notice

⚠️ Automating certain web services may violate their Terms of Service.  Examples include:
- Services requiring explicit API authorization
- Services with automated access restrictions
- Third-party account automation

**Use this tool responsibly.** You are responsible for ensuring your use complies with applicable Terms of Service and laws.

## Known Limitations

### Anti-Bot Detection

Many websites employ anti-bot detection mechanisms such as:
- **CAPTCHA / reCAPTCHA**: Requires manual interaction (not automated)
- **Rate limiting**: May throttle or block requests if too many are made in short intervals
- **Browser fingerprinting**: May block headless browsers or detect automation
- **JavaScript-heavy pages**: Content rendered dynamically may not be immediately available

**Mitigation strategies:**
- Use realistic delays between actions (`wait_for` before interactions)
- Maintain authentic browser context with saved sessions (`auth_context_path`)
- Test workflows against target sites before production use
- Keep browser automation libraries updated

If your workflow encounters a CAPTCHA or is blocked by anti-bot measures, you may need to:
1. Add manual resolution steps or use a CAPTCHA-solving service (beyond scope of this tool)
2. Implement exponential backoff for retry logic
3. Use rotating proxies or sessions for repeated access

## Contributing

Contributions welcome! Please ensure code follows project standards:
- Use type hints
- Add docstrings in English
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation as needed

## License

MIT License - See [LICENSE](LICENSE) file for details.
