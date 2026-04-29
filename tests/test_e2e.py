import pytest
import allure
from utils.performance import save_performance_report
from utils.report_generator import generate_html_report
from workflows import (
    app_context, 
    search_books_by_title_under_year, 
    add_books_to_reading_list, 
    assert_reading_list_count
)

class TestOpenLibrary:
    """
    E2E Test Suite for OpenLibrary Reading List Management.
    Architecture: POM + Workflow Orchestration Layer + Context-Aware Execution.
    """

    @pytest.fixture(autouse=True, scope="function")
    async def setup_test_context(self, app):
        """
        Orchestrates test lifecycle: context injection, state initialization, and automatic cleanup.
        """
        # Inject the 'app' instance into a Task-Local context for standalone workflow functions.
        # This decouples business logic from the Test Class instance (self).
        token = app_context.set(app)

        # Map required configuration to the test instance for readability.
        self.logger = app["logger"]
        self.data = app["config"]["test_data"]
        self.login_page = app["login"]
        
        # Centralizing Auth credentials from the unified app config.
        self.username = app["config"]["auth"]["username"]
        self.password = app["config"]["auth"]["password"]
        self.display_name = app["config"]["auth"]["display_name"]

        yield 

        # Graceful Teardown: Ensures state cleanup and report generation regardless of test outcome.
        try:
            await self._perform_cleanup(app)
        finally:
            # Releasing the context token to prevent memory leaks or context pollution.
            app_context.reset(token)

    async def _perform_cleanup(self, app):
        """
        Handles post-execution tasks: Data sanitization and Performance reporting.
        """
        self.logger.info(f"Teardown: Reverting account state for user: {self.display_name}")
        
        try:
            # Ensuring the account is clean for the next test iteration.
            await app["reading_list"].clear_reading_lists(self.display_name)
        except Exception as e:
            self.logger.warning(f"Non-critical cleanup failure: {e}")
        
        # Consolidating telemetry from all Page Objects for a unified performance insight.
        perf_data = (
            app["search"].performance_data +
            app["book"].performance_data +
            app["reading_list"].performance_data
        )
        
        # Persistence and visualization of collected metrics.
        save_performance_report(perf_data)
        generate_html_report(perf_data)

    @allure.title("E2E: Search and Manage Reading Lists")
    @pytest.mark.asyncio
    async def test_open_library_e2e(self):
        """
        High-level E2E scenario: Verifies book discovery and reading list synchronization.
        Complies with Specification Requirements for standalone function invocation.
        """
        
        # Step A: Authentication via Direct Page Object Interaction.
        await self.login_page.login(self.username, self.password)

        # Step B: Book Discovery - Invoking standalone workflow with Spec-compliant signature.
        found_books = await search_books_by_title_under_year(
            self.data["search_query"],
            self.data["max_year"],
            self.data.get("results_limit", 5)
        )

        # Validating Search Integrity before proceeding.
        assert len(found_books) > 0, f"Zero results for '{self.data['search_query']}' before {self.data['max_year']}"

        # Step C: List Management & Verification.
        await add_books_to_reading_list(found_books)
        
        # Step D: Final Integrity Check - Synchronizing backend state with expected counts.
        await assert_reading_list_count(len(found_books))