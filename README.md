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
├── scripts/
│   └── save_auth.py            # Save browser session for authenticated workflows
├── workflows/                  # Workflow YAML files
├── tests/                      # Unit and integration tests
├── output/                     # Results and logs output
├── auth/                       # Saved browser sessions (auth/{name}.json)
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

- **scripts/save_auth.py**: Session helper — opens a visible browser for manual login and saves the resulting session to `auth/{name}.json`

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
auth: example_auth # only needed for workflows that require authentication — see "Authentication" section below
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
- ✅ Session-based authentication (`auth` field in workflow YAML + `save_auth.py`)
- ✅ Advanced waiting strategies:
  - `wait_for` — DOM element presence
  - `wait_for_hidden` — Element disappearance (for loading spinners)
  - `wait_for_load_state` — Page load states (`networkidle` for SPAs)
  - `wait_for_response` — Network request/response synchronization
- ✅ Flexible text extraction:
  - `extract_text` — Raw text (whitespace collapsed)
  - `extract_inner_text` — Formatted text (layout preserved)

### Future Enhancements
- 🔄 Output file writing
- 🔄 Security measures
- 🔄 Workflow composition (nested workflows)
- 🔄 Additional action types
- 🔄 CI/CD integration examples

## Environment Variables and Secrets (.env)

You can use environment variable files (`.env`) to securely inject secrets (like usernames and passwords) into your workflows without writing them in the YAML or passing them on the command line.

**How it works:**

- You can have multiple `.env` files (e.g., `envs/.env.example`, `envs/.env.othersite`, etc.)
- When running a workflow, pass the desired file with `--env`:
  ```bash
  python src/main.py workflows/example.yaml --env envs/.env.example
  ```
- Placeholders like `{{EXAMPLE_USER}}` and `{{EXAMPLE_PASS}}` are automatically resolved from the `.env` if not passed as a parameter.
- If a parameter is passed via `--param`, it takes precedence over the `.env` value.
- If the placeholder is not found in either, an error is raised.

**Security warning:**
- The `envs/` folder is in `.gitignore` and not committed to git, but `.env` files contain sensitive data. If you share the system, other local users could read them. Use best practices and delete `.env` files when not needed.

**Example .env:**
```
EXAMPLE_USER=my user
EXAMPLE_PASS=my password
```

**Example usage in workflow YAML:**
```yaml
steps:
  - action: fill
    selector: "#username"
    value: "{{EXAMPLE_USER}}"
  - action: fill
    selector: "#password"
    value: "{{EXAMPLE_PASS}}"
```

You can have as many `.env` files as you want and choose which to use for each run.

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

### Action Parameters

| Action                   | Required Parameters                |
|--------------------------|------------------------------------|
| goto                     | url                                |
| fill                     | selector, value                    |
| click                    | selector                           |
| select                   | selector, value                    |
| wait_for                 | selector                           |
| wait_for_hidden          | selector                           |
| wait_for_load_state      | state                              |
| wait_for_response        | url_pattern                        |
| press_key                | selector, key                      |
| extract_text             | selector                           |
| extract_inner_text       | selector                           |
| extract_html             | selector                           |
| extract_attribute_value  | selector, attribute                |
| screenshot               | path                               |

- `goto`: Navigate to a URL
- `fill`: Fill form inputs
- `click`: Click on elements
- `select`: Select dropdown options
- `wait_for`: Wait for element to appear in the DOM
- `wait_for_hidden`: Wait for element to disappear from the DOM or become hidden
- `wait_for_load_state`: Wait for page to reach a load state (`domcontentloaded`, `load`, `networkidle`)
- `wait_for_response`: Wait for a network response matching a URL pattern
- `press_key`: Press a keyboard key on an element
- `extract_text`: Extract raw text content from elements (whitespace collapsed, no layout)
- `extract_inner_text`: Extract text preserving layout (newlines for paragraphs, lists, blocks)
- `extract_html`: Extract HTML from elements
- `extract_attribute_value`: Extract the value of an attribute from an element (e.g., value of an input)
- `screenshot`: Take a screenshot

### `extract_text` vs `extract_inner_text`

| | `extract_text` | `extract_inner_text` |
|---|---|---|
| Playwright method | `page.text_content()` | `page.inner_text()` |
| Whitespace/newlines | Collapsed | Preserved (follows CSS layout) |
| Hidden elements | Included | Excluded |
| Use when | Simple string extraction | Structured responses (paragraphs, lists) |

### Waiting Strategies (`wait_for_*`)

Different wait strategies are optimized for different scenarios:

#### `wait_for` — Wait for Element in DOM
Waits for an element to appear in the DOM.
```yaml
- action: wait_for
  selector: ".content"
```
**Use when:** Polling for content on already-loaded pages, simple DOM changes.

#### `wait_for_hidden` — Wait for Element to Disappear
Waits for an element to either become invisible (`display: none`) or be removed from the DOM entirely. Essential for synchronizing with loading spinners.
```yaml
- action: wait_for
  selector: ".loading-spinner"

- action: wait_for_hidden
  selector: ".loading-spinner"

- action: extract_inner_text
  selector: ".result"
```
**Use when:** Waiting for async operations (API calls, data generation) marked by loading indicators.

#### `wait_for_load_state` — Wait for Page Load State
Waits for the page to reach a specific load state. This is critical for Single Page Applications (SPAs) like Angular or React.

States:
- `domcontentloaded` — DOM fully parsed (fastest, for static pages)
- `load` — `window.onload` event fired
- `networkidle` — No pending network requests for 500ms (most robust for SPAs)

```yaml
- action: goto
  url: "https://app.example.com"

- action: wait_for_load_state
  state: networkidle  # Ensures Angular/React has finished initialization
```
**Use when:** Following `goto` to ensure the framework has initialized before interacting with dynamic elements.

#### `wait_for_response` — Wait for Network Response
Waits for a specific HTTP response matching a URL pattern.

```yaml
- action: wait_for_response
  url_pattern: "**/api/generate**"  # Glob pattern
  timeout: 60000                     # Optional, ms (default: 30000)
```
**Use when:** Confirming that a server has processed a request (e.g., confirming API response before extracting data).

**Note:** For streaming responses, this waits for the first response chunk. If complete content transmission is needed, combine with `wait_for_hidden` (for loading indicators) or `wait_for_selector` (for completion markers).

## Legal Notice

⚠️ **Automating web services involves important legal considerations.** You are responsible for ensuring your use complies with applicable Terms of Service and laws.

### Web Automation and Terms of Service

Many web services prohibit automated access in their Terms of Service (ToS). Examples include:
- Services requiring explicit API authorization
- Services with explicit automated access restrictions  
- Third-party account automation or scraping
- Unauthorized access to accounts or systems

**Always review the Terms of Service** of any third-party service before automating access to it.

### Third-Party Services and Legal Compliance

When using webflow-mcp to automate web applications:

- **You are solely responsible** for verifying that your usage complies with the service's ToS
- **Unauthorized access** to accounts, systems, or data may violate computer fraud laws:
  - US: Computer Fraud and Abuse Act (CFAA)
  - EU: Computer Misuse Directive and national laws
  - Other jurisdictions have similar regulations
- **At-scale automation** (mass scraping, distributed attacks) may be illegal regardless of ToS

### Permitted Uses

Use webflow-mcp responsibly for:
- Automating your own accounts and personal data
- Services you own or operate
- Internal, development, or testing purposes with explicit authorization
- Services with explicit automation policies (e.g., those providing APIs)

### Sessions and Credentials

- Auth sessions saved by `save_auth.py` contain browser credentials (cookies, tokens)
- **Never commit auth files to version control** — add `auth/` to `.gitignore`
- Treat saved sessions as you would treat passwords and API keys
- Sessions are site-specific and will expire according to the service's session policy

## Authentication

Some workflows require an authenticated browser session (e.g. services that require login). webflow-mcp handles this via saved sessions — you log in once manually, and the session is reused for subsequent automated runs.

### Saving a Session

Run the following command to open a visible browser, log in manually, and save the session:

```bash
python scripts/save_auth.py --url https://example.com --name mysite
```

- `--url`: The page to navigate to for login
- `--name`: Name for the saved session (e.g. `mysite` → saved as `auth/mysite.json`)

Once the browser opens, complete the login process (including any 2FA or OAuth steps). When finished, press Enter in the terminal. The session is saved automatically.

> **Note:** Sessions saved this way include cookies and browser storage (localStorage, sessionStorage). They are site-specific and will expire when the site's session expires — typically days to weeks. Re-run `save_auth.py` when a session expires.

> ⚠️ **Disclaimer:**
> - Some websites (especially Google, Microsoft, and banking sites) actively detect browser automation and may block or invalidate sessions created with Playwright, even when using persistent profiles. Session persistence is not guaranteed for all sites.
> - If you experience repeated logouts or detection, try using the latest Playwright version, avoid headless mode, and ensure your browser profile is not shared between manual and automated runs.
> - This tool is intended for ethical automation of your own accounts or with explicit permission. Respect all terms of service and legal requirements.

### Using a Session in a Workflow

Reference the session name in your workflow YAML via the `auth` field:

```yaml
name: my_workflow
auth: mysite  # loads auth/mysite.json
steps:
  - action: goto
    url: "https://example.com/dashboard"
```

If the `auth` field is omitted, the workflow runs without authentication. If `auth` is set but the corresponding file does not exist, the workflow will fail with a `FileNotFoundError` — run `save_auth.py` first.

> ⚠️ **Security:** Auth files contain sensitive session data (cookies). Do not commit `auth/` to version control. This folder is listed in `.gitignore`.

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

MIT License - See [LICENSE] file for details.
