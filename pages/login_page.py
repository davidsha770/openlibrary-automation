import re
import logging
from playwright.async_api import expect, Page
from .base_page import BasePage

class LoginPage(BasePage):
    """
    Handles authentication flows for Open Library.
    Optimized for bypassing security challenges and robust session verification.
    """
    def __init__(self, page: Page, logger: logging.Logger, config: dict):
        super().__init__(page, logger, config)

    # --- Selectors ---
    # Email/Username inputs with fallback options for UI variations
    EMAIL_INPUT = "input[name='email'], input[name='username'], input[id='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[name='login']"
    
    # Selectors for human-verification challenges (e.g., Cloudflare, Turnstile)
    CHALLENGE_SELECTORS = [
        "button:has-text('Verify')", 
        "button:has-text('human')", 
        "#cf-turnstile-identity",
        "div.ctp-checkbox-container"
    ]
    
    # Elements indicating a successful authenticated state
    SUCCESS_INDICATOR = "a[href*='/people/'], .manage-menu-button, button:has-text('Log Out')"

    async def navigate(self):
        """Technical Action: Direct navigation to the login entry point."""
        login_url = f"{self.config['urls']['base_url'].rstrip('/')}/account/login"
        await self.page.goto(login_url, wait_until="domcontentloaded")

    async def fill_credentials(self, email, password):
        """Technical Action: populates the authentication form and submits."""
        await self.page.locator(self.EMAIL_INPUT).first.fill(email)
        await self.page.locator(self.PASSWORD_INPUT).fill(password)
        await self.page.click(self.SUBMIT_BUTTON)

    async def is_logged_in(self) -> bool:
        """
        Technical Verification: Returns True/False based on URL and UI state.
        This method avoids raising exceptions to allow flexible workflow handling.
        """
        try:
            # Verify URL transition to an authenticated endpoint
            await expect(self.page).to_have_url(re.compile(r".*/(account|people|books).*"), timeout=10000)
            # Verify visibility of account-specific UI elements
            return await self.page.locator(self.SUCCESS_INDICATOR).first.is_visible()
        except Exception:
            return False

    async def handle_security_challenges(self):
        """
        Technical Utility: Iterates through known challenge selectors to clear verification overlays.
        Utilizes forced clicks to bypass potential interception.
        """
        for selector in self.CHALLENGE_SELECTORS:
            locator = self.page.locator(selector)
            # Check for existence and visibility before interaction
            if await locator.count() > 0 and await locator.first.is_visible():
                self.logger.info(f"Security challenge detected: {selector}. Attempting clearance...")
                try:
                    # force=True is used to interact with elements that may be partially obscured
                    await locator.first.click(timeout=5000, force=True)
                    # Brief synchronization delay to allow for potential page reloads
                    await self.page.wait_for_timeout(2000)
                except Exception as e:
                    self.logger.debug(f"Failed to clear challenge via {selector}: {e}")