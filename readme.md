# Open Library E2E Automation & Performance Suite

A high-performance End-to-End (E2E) testing framework for [Open Library](https://openlibrary.org). This project uses **Python**, **Playwright**, and **Asyncio** to automate user flows while benchmarking site performance.

## 🌟 Key Features

* **Asynchronous Architecture**: Built with `asyncio` for fast, non-blocking execution.
* **Page Object Model (POM)**: Organized into reusable and maintainable page classes.
* **Performance Tracking**: Captures real-time metrics (Load Time, DOM Content Loaded, First Paint) using the Browser Navigation Timing API.
* **Dynamic Element Handling**: Employs Playwright’s native auto-waiting and semantic locators to reliably interact with complex, asynchronous UI components without the need for fragile scripts.
* **State-Aware Cleanup Mechanism**: Includes a robust teardown suite that programmatically clears user reading lists, ensuring environmental consistency and idempotent test execution.
* **Headless Execution**: Configured to run in the background for efficiency.
* **Comprehensive Reporting**: Generates both a custom-built performance HTML report and professional Allure reports for detailed test execution analytics.
* **Full POM Decoupling**: 100% separation between test logic and UI selectors, ensuring zero selectors in the test scripts.

* **Post-Action Verification:** Explicit logic to verify login success and confirm list updates before proceeding, ensuring high test reliability
* **Automated Authentication Resilience**: Features a dedicated security challenge handler that detects and manages bot-prevention overlays (e.g., Turnstile/Cloudflare) to ensure uninterrupted CI/CD flows.

## 📁 Project Structure

```text
.
├── config/
│   └── config.json           # Test parameters (search query, performance thresholds)
├── pages/
│   ├── base_page.py          # Abstract Page Object with common actions
│   ├── login_page.py         # Dedicated login POM
│   ├── search_page.py        # Search and filtering functionality
│   ├── book_page.py          # Book-specific actions & JS injections
│   └── reading_list_page.py  # Reading list hydration and verification
├── tests/
│   └── test_e2e.py           # Test orchestrator (100% Logic, 0% Selectors)
├── utils/
│   ├── utils/decorators.py   # Custom Python decorators for retry logic
│   ├── logger_helper.py      # Custom logging configuration
│   ├── performance.py        # Dedicated Performance Monitoring (SRP)
│   └── report_generator.py   # Logic for HTML report generation
├── outputs/
│   ├── report.html           # Visual HTML report
│   ├── screenshots/          # Action confirmation captures
│   └── performance_report.json # Final performance benchmark report
├── requirements.txt          # Project dependencies
├── conftest.py               # Shared fixtures and Playwright setup
├── pytest.ini                # Pytest configuration (Async mode, etc.)
├── ReadMeAIBugs.md           # Static analysis report
├── .env                      # Secure environment variables (ignored by git)
├── .env.example
└── README.md                 # This file

```

## 🛠️ Setup & Installation

### 1. Clone the Repository
```bash
git clone openlibrary-automation
cd openlibrary_automation
```

### 2. Environment Setup

It is recommended to use a virtual environment:
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

### 3. Configure Credentials
Create a `.env` file in the root directory:
```env
OL_USERNAME=your mail
OL_PASSWORD=your password
OL_DISPLAY_NAME=your username
```

## 🚦 Running the Automation


```Bash
# Execute the full E2E flow with Pytest
pytest -v -s --alluredir=allure-results

# To view the Allure report after execution:
allure serve allure-results

# Generate a static Allure report
allure generate allure-results --clean -o allure-report
```

This will:

    Initialize the Playwright environment.

    Execute the test suite.

    Generate an interactive report at outputs/report.html.

> **Note:** The script is currently configured to run in **Headless** mode.

## 📊 Reporting & Evidence

The framework produces a high-quality audit trail for every execution:

* **Visual HTML Report**: Located at `outputs/report.html`, this standalone report displays:
    * **Performance Metrics**: Color-coded status (Pass/Warn) for page load times against pre-defined thresholds.
    * **Visual Evidence Grid**: A gallery of screenshots captured during the "Add to List" flow.
* **Performance Benchmarking**: The `performance_report.json` provides raw data for CI/CD integration, tracking metrics from the Navigation Timing API.
* **Automated Documentation**: Screenshots are named dynamically based on book titles (e.g., `Dune.png`) for easy traceability.

## 🛠️ Architecture Highlights

* **Robust Login Flow**: Isolated `LoginPage` handling with explicit waits for UI readiness.
* **Smart Filtering**: The `SearchPage` encapsulates the logic for traversing search results, extracting metadata (Regex-based), and handling pagination until the requested quota is met.
* **Utility-Driven Design**: Logging and reporting logic are decoupled into a `utils` package, following the Single Responsibility Principle.

## 📸 Artifacts
* **Screenshots**: Automatically saved to `outputs/screenshots/` upon successful actions or verification steps.
* **Logs**: Comprehensive execution logs are streamed to the console for real-time monitoring.

* **Test Runner**: Powered by Pytest with pytest-playwright integration for robust fixture management and test orchestration.

* **Dynamic Configuration**: Environment-aware execution using python-dotenv for sensitive credentials and config.json for test parameters

## 🛡️ Stability & Resilience Patterns

This framework implements a multi-layered approach to handle the inherent flakiness of web automation:

* **Logic-Based Retries**: Critical actions (Login, Book Addition) are wrapped in a custom `@retry_on_failure` decorator to mitigate transient network issues or UI lags.
* **State-Change Verification**: Instead of simple visibility checks, the suite validates UI state transitions (e.g., verifying the `.activated` CSS class) to ensure the backend has processed the request.
* **Synchronized Polling**: The assertion logic for reading list counts employs a smart-polling strategy with periodic page reloads to ensure the DOM is synced with the server-side state.
* **Normalized URL Navigation**: A custom navigation utility prevents redundant page reloads by normalizing URLs (handling trailing slashes and query parameters), optimizing both speed and performance metric accuracy.

```markdown
🧩 Challenges & Solutions

    Advanced Async Orchestration: Integrated Playwright's asynchronous API with a class-based Pytest structure. This leverages professional fixtures for clean setup/teardown while maintaining high-speed, non-blocking execution.

    Authentication Resilience: Open Library implements Cloudflare/Turnstile challenges. The framework features a dedicated _handle_security_challenges utility that detects and interacts with verification overlays to ensure uninterrupted CI/CD flows.

    State-Aware Teardown & Idempotency: To ensure environmental consistency, the framework implements a robust cleanup mechanism that programmatically clears reading lists. Instead of fixed timers, it utilizes a Smart-Wait strategy—combining Playwright’s Web-First Assertions with periodic Page Refreshes. This handles "eventual consistency" issues where the UI might lag behind server-side updates, ensuring a pristine state for subsequent test cycles and preventing data pollution.

    High-Accuracy Benchmarking: Instead of deprecated methods, the suite implements the Navigation Timing API (Level 2). It calculates durations by subtracting startTime from event timestamps, providing precise, modern metrics for performance auditing.
```

## 📝 License
This project is for educational and testing purposes.

## 📋 Requirements
* Python 3.9+
* Pytest 8.0+
* Playwright 1.40+
* Allure-Pytest
* Open Library Account (for Login/List functionality)

## 🔍 Source Code Analysis
A detailed static analysis of the original boilerplate code, including identified bugs (Critical/Major) and structural improvements, can be found in [ReadMeAIBugs.md](./ReadMeAIBugs.md).