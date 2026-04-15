from pages.base_page import BasePage
import asyncio

class LoginPage(BasePage):
    """
    Handles authentication flows for Open Library.
    Includes automated handling for 'Verify you are human' challenges and robust session verification.
    """
    # Selectors
    USERNAME_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[name='login']"
    
    # Challenge Handling
    VERIFY_HUMAN_BTN = "#verify-human-btn"
    
    # Combined success indicators
    SUCCESS_INDICATOR = ".manage-menu-button, #user-menu-button, a[href*='/people/']"

    async def login(self, username, password):
        """
        Executes the full login sequence, including automated handling of security challenges.
        """
        try:
            self.logger.info("Navigating to login page...")
            await self.page.goto("https://openlibrary.org/account/login", wait_until="networkidle")
            
            # --- Handling the 'Verify you are human' challenge ---
            # We check if the verification button is present before proceeding to login
            verify_btn = self.page.locator(self.VERIFY_HUMAN_BTN)
            if await verify_btn.is_visible(timeout=5000):
                self.logger.info("Security challenge detected. Attempting to verify...")
                
                # We use a deliberate wait and scroll to simulate human-like interaction
                await verify_btn.scroll_into_view_if_needed()
                await asyncio.sleep(1) 
                await verify_btn.click()
                
                # Wait for the challenge to resolve and redirect/refresh
                self.logger.info("Challenge button clicked. Waiting for verification to complete...")
                await self.page.wait_for_load_state("networkidle")

            # --- Standard Login Flow ---
            await self.page.wait_for_selector(self.USERNAME_INPUT, state="visible", timeout=15000)
            await self.page.fill(self.USERNAME_INPUT, username)
            await self.page.fill(self.PASSWORD_INPUT, password)
            
            self.logger.info("Credentials filled, submitting form...")
            
            async with self.page.expect_navigation(wait_until="domcontentloaded", timeout=45000):
                await self.page.click(self.SUBMIT_BUTTON)

            # Session Verification
            self.logger.info("Verifying session readiness...")
            success_element = self.page.locator(self.SUCCESS_INDICATOR).first
            await success_element.wait_for(state="visible", timeout=15000)
            
            self.logger.info("Login sequence successfully verified.")

        except Exception as e:
            # Fallback for failed verification or wrong credentials
            error_locator = self.page.locator(".error, .alert-danger")
            if await error_locator.is_visible():
                msg = await error_locator.inner_text()
                self.logger.error(f"Application-level error: {msg}")
            
            await self.page.screenshot(path="outputs/login_error.png")
            self.logger.error(f"Critical failure during login sequence: {e}")
            raise e