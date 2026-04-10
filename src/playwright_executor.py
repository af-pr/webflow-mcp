"""
Playwright automation executor

This module provides the PlaywrightExecutor class for automating web workflows
using Playwright and handling step execution, validation, and logging.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from src.models import Step, StepResult, ActionType, Workflow

AUTH_DIR = Path(__file__).parent.parent / "auth"

class PlaywrightExecutor:
    """Execute web automation workflows using Playwright"""
    
    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000
    ):
        """
        Initialize PlaywrightExecutor
        
        Args:
            headless: Run browser in headless mode (no GUI)
            timeout: Timeout in milliseconds for page operations
        """
        self.logger = logging.getLogger(__name__)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        
        # Map actions to handler methods
        self.actions = {
            ActionType.GOTO: self._handle_goto,
            ActionType.FILL: self._handle_fill,
            ActionType.CLICK: self._handle_click,
            ActionType.SELECT: self._handle_select,
            ActionType.WAIT_FOR: self._handle_wait_for,
            ActionType.WAIT_FOR_HIDDEN: self._handle_wait_for_hidden,
            ActionType.WAIT_FOR_LOAD_STATE: self._handle_wait_for_load_state,
            ActionType.WAIT_FOR_RESPONSE: self._handle_wait_for_response,
            ActionType.EXTRACT_TEXT: self._handle_extract_text,
            ActionType.EXTRACT_INNER_TEXT: self._handle_extract_inner_text,
            ActionType.EXTRACT_HTML: self._handle_extract_html,
            ActionType.SCREENSHOT: self._handle_screenshot,
            ActionType.PRESS_KEY: self._handle_press_key,
        }
        
        self.logger.info("PlaywrightExecutor initialized")
    
    def __enter__(self) -> "PlaywrightExecutor":
        """Context manager entry"""
        self._start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure browser is closed"""
        self.close()
        return False
    
    def _start_browser(self) -> None:
        """Start Playwright and launch browser"""
        self.logger.debug("Starting browser...")
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.logger.info("Browser started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            raise

    def _create_context(self, workflow: Workflow) -> None:
        """Create browser context, loading auth session if specified in the workflow.

        Args:
            workflow: Workflow object — if workflow.auth is set, loads auth/{name}.json

        Raises:
            FileNotFoundError: If workflow.auth is set but the auth file does not exist
        """
        if workflow.auth:
            auth_path = AUTH_DIR / f"{workflow.auth}.json"
            if not auth_path.exists():
                raise FileNotFoundError(
                    f"Auth file not found: {auth_path}. "
                    f"Run 'python scripts/save_auth.py --name {workflow.auth} --url <url>' to create it."
                )
            self.logger.info(f"Loading auth session from {auth_path}")
            self.context = self.browser.new_context(storage_state=str(auth_path))
        else:
            self.logger.debug("Creating new browser context without auth")
            self.context = self.browser.new_context()

        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        self.logger.info("Browser context created successfully")
    
    def close(self) -> None:
        """Close browser and cleanup resources"""
        self.logger.debug("Closing Playwright...")
        
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.logger.info("Playwright closed successfully")
        
        except Exception as e:
            self.logger.error(f"Error closing Playwright: {e}")
    
    def _validate_step(self, step: Step) -> None:
        """Validate that a step has all required parameters"""
        step.validate()
    
    def execute_workflow(self, workflow: Workflow) -> List[StepResult]:
        """
        Execute a workflow
        
        Args:
            workflow: Workflow object to execute
        
        Returns:
            List of StepResult objects

        Raises:
            FileNotFoundError: If workflow.auth is set but the auth file does not exist
        """
        self._create_context(workflow)
        self.logger.info(f"Executing workflow '{workflow.name}' with {len(workflow.steps)} steps")
        results = []
        
        for idx, step in enumerate(workflow.steps):
            try:
                self._validate_step(step)
                
                self.logger.debug(f"Executing step {idx + 1}: {step.action.value}")
                result = self._execute_step(step)
                results.append(result)
                
                if not result.success:
                    self.logger.warning(f"Step {idx + 1} failed: {result.error}")
            
            except Exception as e:
                self.logger.error(f"Step {idx + 1} raised exception: {e}")
                results.append(StepResult(success=False, error=str(e)))
        
        return results
    
    def _execute_step(self, step: Step) -> StepResult:
        """Execute a single step"""
        if step.action not in self.actions:
            return StepResult(
                success=False,
                error=f"Unknown action: {step.action.value}"
            )
        
        handler = self.actions[step.action]
        return handler(step)
    
    # ========================================================================
    # Action Handlers
    # ========================================================================
    
    def _handle_goto(self, step: Step) -> StepResult:
        """Navigate to a URL"""
        try:
            url = step.params["url"]
            self.logger.debug(f"Navigating to {url}")
            self.page.goto(url, wait_until="networkidle")
            self.logger.info(f"Successfully navigated to {url}")
            
            return StepResult(success=True, data={"url": url})
        
        except Exception as e:
            error_msg = f"Navigation failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)
    
    def _handle_fill(self, step: Step) -> StepResult:
        """Fill a form input with text"""
        try:
            selector = step.params["selector"]
            value = step.params["value"]
            
            self.logger.debug(f"Filling '{selector}' with '{value}'")
            self.page.fill(selector, value)
            self.logger.info(f"Successfully filled '{selector}'")
            
            return StepResult(success=True, data={"selector": selector})
        
        except Exception as e:
            error_msg = f"Fill failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)
    
    def _handle_click(self, step: Step) -> StepResult:
        """Click on an element"""
        try:
            selector = step.params["selector"]
            
            self.logger.debug(f"Clicking on '{selector}'")
            self.page.click(selector)
            self.logger.info(f"Successfully clicked on '{selector}'")
            
            return StepResult(success=True, data={"selector": selector})
        
        except Exception as e:
            error_msg = f"Click failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)
    
    def _handle_select(self, step: Step) -> StepResult:
        """Select an option from a dropdown"""
        try:
            selector = step.params["selector"]
            value = step.params["value"]
            
            self.logger.debug(f"Selecting '{value}' in '{selector}'")
            self.page.select_option(selector, value)
            self.logger.info(f"Successfully selected in '{selector}'")
            
            return StepResult(success=True, data={"selector": selector, "value": value})
        
        except Exception as e:
            error_msg = f"Select failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)
    
    def _handle_wait_for(self, step: Step) -> StepResult:
        """Wait for an element to appear"""
        try:
            selector = step.params["selector"]
            
            self.logger.debug(f"Waiting for '{selector}'")
            self.page.wait_for_selector(selector)
            self.logger.info(f"Element '{selector}' appeared")
            
            return StepResult(success=True, data={"selector": selector})
        
        except Exception as e:
            error_msg = f"Wait failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)

    def _handle_wait_for_hidden(self, step: Step) -> StepResult:
        """Wait for an element to disappear (become hidden or detached from the DOM).

        Useful for waiting on loading spinners or progress indicators to finish
        before extracting content. Uses Playwright's state='hidden' which covers
        both elements that become invisible (display:none) and those removed from DOM.
        """
        try:
            selector = step.params["selector"]

            self.logger.debug(f"Waiting for '{selector}' to be hidden")
            self.page.wait_for_selector(selector, state="hidden")
            self.logger.info(f"Element '{selector}' is now hidden")

            return StepResult(success=True, data={"selector": selector})

        except Exception as e:
            error_msg = f"Wait for hidden failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)

    def _handle_wait_for_load_state(self, step: Step) -> StepResult:
        """Wait for the page to reach a specific load state.

        States:
        - 'domcontentloaded': DOM fully parsed (fastest, for static pages)
        - 'load': window.onload event has fired
        - 'networkidle': no pending network requests for 500ms (robust for SPAs like Angular/React)

        Useful after goto() to ensure the framework (Angular, React, etc.) has finished
        initializing before interacting with dynamic elements.
        """
        try:
            state = step.params["state"]

            self.logger.debug(f"Waiting for page to reach '{state}' state")
            self.page.wait_for_load_state(state)
            self.logger.info(f"Page reached '{state}' state")

            return StepResult(success=True, data={"state": state})

        except Exception as e:
            error_msg = f"Wait for load state failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)

    def _handle_wait_for_response(self, step: Step) -> StepResult:
        """Wait for a network response matching a URL pattern.

        Useful for waiting on API responses before extracting data.
        Patterns can be glob (e.g., '**/api/generate**') or regex.
        
        Parameters:
        - url_pattern: URL pattern to match (glob or regex)
        - timeout (optional): Max milliseconds to wait (default: 30000)

        Note: Useful for confirming network activity, but individual network
        responses in streaming don't guarantee complete content.
        """
        try:
            url_pattern = step.params["url_pattern"]
            timeout = step.params.get("timeout", 30000)

            self.logger.debug(f"Waiting for response matching '{url_pattern}'")
            response = self.page.wait_for_response(url_pattern, timeout=timeout)
            self.logger.info(f"Received response with status {response.status} for '{url_pattern}'")

            return StepResult(success=True, data={
                "url_pattern": url_pattern,
                "status": response.status,
                "url": response.url
            })

        except Exception as e:
            error_msg = f"Wait for response failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)
    
    def _handle_extract_text(self, step: Step) -> StepResult:
        """Extract raw text from an element (no whitespace or layout preservation)"""
        try:
            selector = step.params["selector"]
            
            self.logger.debug(f"Extracting text from '{selector}'")
            text = self.page.text_content(selector)
            self.logger.info(f"Successfully extracted text from '{selector}'")
            
            return StepResult(success=True, data={"text": text})
        
        except Exception as e:
            error_msg = f"Extract text failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)

    def _handle_extract_inner_text(self, step: Step) -> StepResult:
        """Extract formatted text from an element, preserving layout (newlines, list structure).

        Uses Playwright's inner_text() which respects CSS rendering:
        - Block elements (<div>, <p>, <li>) produce newlines
        - Hidden elements are excluded
        - More readable output than text_content() for complex HTML
        """
        try:
            selector = step.params["selector"]

            self.logger.debug(f"Extracting inner text from '{selector}'")
            text = self.page.inner_text(selector)
            self.logger.info(f"Successfully extracted inner text from '{selector}'")

            return StepResult(success=True, data={"text": text})

        except Exception as e:
            error_msg = f"Extract inner text failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)
    
    def _handle_extract_html(self, step: Step) -> StepResult:
        """Extract HTML from an element"""
        try:
            selector = step.params["selector"]
            
            self.logger.debug(f"Extracting HTML from '{selector}'")
            html = self.page.inner_html(selector)
            self.logger.info(f"Successfully extracted HTML from '{selector}'")
            
            return StepResult(success=True, data={"html": html})
        
        except Exception as e:
            error_msg = f"Extract HTML failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)
    
    def _handle_screenshot(self, step: Step) -> StepResult:
        """Take a screenshot"""
        try:
            path = step.params["path"]
            
            self.logger.debug(f"Taking screenshot to '{path}'")
            self.page.screenshot(path=path)
            self.logger.info(f"Screenshot saved to '{path}'")
            
            return StepResult(success=True, data={"path": path})
        
        except Exception as e:
            error_msg = f"Screenshot failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)
    
    def _handle_press_key(self, step: Step) -> StepResult:
        """Press a key on a focused element"""
        try:
            selector = step.params["selector"]
            key = step.params["key"]
            
            self.logger.debug(f"Pressing key '{key}' on '{selector}'")
            self.page.press(selector, key)
            self.logger.info(f"Successfully pressed key '{key}' on '{selector}'")
            
            return StepResult(success=True, data={"selector": selector, "key": key})
        
        except Exception as e:
            error_msg = f"Press key failed: {e}"
            self.logger.error(error_msg)
            return StepResult(success=False, error=error_msg)  
