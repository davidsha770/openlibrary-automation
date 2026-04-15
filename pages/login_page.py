from pages.base_page import BasePage

class LoginPage(BasePage):
    """
    Handles authentication flows for Open Library.
    Includes robust session verification and error handling for failed attempts.
    """
    # Selectors
    USERNAME_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[name='login']"
    
    # Combined success indicators to avoid Strict Mode Violations.
    # Targets either the management menu, user button, or a profile link.
    SUCCESS_INDICATOR = ".manage-menu-button, #user-menu-button, a[href*='/people/']"

    async def login(self, username, password):
        """
        Executes the full login sequence.
        Uses a navigation proxy to ensure the session is established before proceeding.
        """
        try:
            self.logger.info("Navigating to login page...")
            await self.page.goto("https://openlibrary.org/account/login", wait_until="networkidle")
            
            # Ensure input fields are ready before interaction
            await self.page.wait_for_selector(self.USERNAME_INPUT, state="visible", timeout=15000)
            await self.page.fill(self.USERNAME_INPUT, username)
            await self.page.fill(self.PASSWORD_INPUT, password)
            
            self.logger.info("Credentials filled, submitting form...")
            
            # Using expect_navigation concurrently with the click to handle the post-login redirect reliably
            async with self.page.expect_navigation(wait_until="domcontentloaded", timeout=45000):
                await self.page.click(self.SUBMIT_BUTTON)

            # Session Verification: Wait for any of the success elements to appear
            self.logger.info("Verifying session readiness...")
            # Use .first to resolve potential multiple matches in the combined selector string
            success_element = self.page.locator(self.SUCCESS_INDICATOR).first
            await success_element.wait_for(state="visible", timeout=15000)
            
            self.logger.info("Login sequence successfully verified.")

        except Exception as e:
            # Failure Analysis: Check for visible error messages from the application UI
            error_locator = self.page.locator(".error, .alert-danger")
            if await error_locator.is_visible():
                msg = await error_locator.inner_text()
                self.logger.error(f"Application-level login error: {msg}")
            
            # Visual evidence capture for debugging
            await self.page.screenshot(path="outputs/login_error.png")
            self.logger.error(f"Critical failure during login sequence: {e}")
            raise e