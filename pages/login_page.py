from pages.base_page import BasePage

class LoginPage(BasePage):
    """
    Page Object for the Open Library Login page.
    """
    # --- Selectors ---
    USERNAME_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    LOGIN_URL = "https://openlibrary.org/account/login"

    async def login(self, username, password):
        """
        Navigates to the login page and performs authentication.
        """
        self.logger.info(f"Navigating to login page: {self.LOGIN_URL}")
        await self.page.goto(self.LOGIN_URL)
        
        # Wait for fields to be ready
        await self.page.wait_for_selector(self.USERNAME_INPUT, state="visible")
        
        # Action
        await self.page.fill(self.USERNAME_INPUT, username)
        await self.page.fill(self.PASSWORD_INPUT, password)
        await self.page.click(self.SUBMIT_BUTTON)
        
        # Wait for navigation to complete after login
        await self.page.wait_for_load_state("networkidle")
        self.logger.info("Login form submitted.")