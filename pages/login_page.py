from playwright.async_api import expect
import re
import logging
from playwright.async_api import Page
from .base_page import BasePage
from utils.decorators import retry_on_failure

class LoginPage(BasePage):
    """
    Handles authentication flows for Open Library.
    Optimized for bypassing security challenges and robust session verification.
    """
    def __init__(self, page: Page, logger: logging.Logger, config: dict):
        super().__init__(page, logger, config)

    # Selectors - Using multiple options for email/username to handle UI variations
    EMAIL_INPUT = "input[name='email'], input[name='username'], input[id='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[name='login']"
    
    # Expanded Challenge Selectors
    CHALLENGE_SELECTORS = [
        "button:has-text('Verify')", 
        "button:has-text('human')", 
        "#cf-turnstile-identity",
        "div.ctp-checkbox-container"
    ]
    
    SUCCESS_INDICATOR = "a[href*='/people/'], .manage-menu-button, button:has-text('Log Out')"

    @retry_on_failure(times=2, delay=5)
    async def login(self, email, password):
        """
        Authenticates the user with built-in retry logic and detailed error reporting.
        The decorator will re-run this entire method if an exception is raised.
        """
        try:
            self.logger.info("Navigating to login page...")
            login_url = f"{self.config['urls']['base_url'].rstrip('/')}/account/login"
            await self.page.goto(login_url, wait_until="domcontentloaded")

            await self._handle_security_challenges()
                
            email_field = self.page.locator(self.EMAIL_INPUT).first
            self.logger.info("Waiting for login inputs to become ready...")
                
            try:
                await expect(email_field).to_be_visible(timeout=30000)
            except AssertionError:
                self.logger.warning("Email input not found. Final attempt to clear challenge...")
                await self._handle_security_challenges()
                await expect(email_field).to_be_visible(timeout=15000)
                
            await email_field.fill(email)
            await self.page.locator(self.PASSWORD_INPUT).fill(password)
            await self.page.click(self.SUBMIT_BUTTON)
                
            # Verification logic
            await expect(self.page).to_have_url(re.compile(r".*/(account|people|books).*"), timeout=20000)
            await expect(self.page.locator(self.SUCCESS_INDICATOR).first).to_be_visible(timeout=15000)
            self.logger.info("Login sequence successfully verified.")

        except Exception as e:
            await self.report_error(e, "Login sequence failed", "login_failure")
            raise e

    async def _handle_security_challenges(self):
        """
        Attempts to find and interact with human-verification elements.
        """
        for selector in self.CHALLENGE_SELECTORS:
            # Check for selectors inside iframes as well
            locators = self.page.locator(selector)
            count = await locators.count()
            
            for i in range(count):
                locator = locators.nth(i)
                if await locator.is_visible():
                    self.logger.info(f"Security challenge found: {selector}. Clicking...")
                    try:
                        # Use force=True to click elements that might be partially covered
                        await locator.click(timeout=5000, force=True)
                        # Wait for potential reload
                        await self.page.wait_for_timeout(2000) 
                    except Exception as e:
                        self.logger.debug(f"Could not click challenge element: {e}")