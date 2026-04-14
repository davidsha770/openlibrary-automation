# Open Library E2E Automation & Performance Suite

A high-performance End-to-End (E2E) testing framework for [Open Library](https://openlibrary.org). This project uses **Python**, **Playwright**, and **Asyncio** to automate user flows while benchmarking site performance.

## 🌟 Key Features

* **Asynchronous Architecture**: Built with `asyncio` for fast, non-blocking execution.
* **Page Object Model (POM)**: Organized into reusable and maintainable page classes.
* **Performance Tracking**: Captures real-time metrics (Load Time, DOM Content Loaded, First Paint) using the Browser Navigation Timing API.
* **Shadow DOM Handling**: Utilizes advanced recursive JavaScript injection to interact with complex Web Components.
* **Smart Library Sync**: Logic to detect current book status (Want to Read / Already Read) to avoid redundant actions.
* **Headless Execution**: Configured to run in the background for efficiency.
* **Advanced Reporting Engine**: Custom-built HTML reporting tool that aggregates performance data and visual evidence (screenshots) into a single, shareable file.

* **Full POM Decoupling**: 100% separation between test logic and UI selectors, ensuring zero selectors in the test scripts.

## 📁 Project Structure

```text
.
├── config/
│   └── config.json           # Credentials, test query, and performance thresholds
├── pages/
│   ├── base_page.py          # Core logic for performance measurement
│   ├── login_page.py         # Dedicated login POM
│   ├── search_page.py        # Search and filtering functionality
│   ├── book_page.py          # Book-specific actions & JS injections
│   └── reading_list_page.py  # Reading list hydration and verification
├── tests/
│   └── test_e2e.py           # Test orchestrator (100% Logic, 0% Selectors)
├── utils/
│   ├── logger_helper.py      # Custom logging configuration
│   └── report_generator.py   # Logic for HTML report generation
├── outputs/
│   ├── report.html           # Visual HTML report
│   ├── screenshots/          # Action confirmation captures
│   └── performance_report.json # Final performance benchmark report
├── requirements.txt          # Project dependencies
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

Update the config/config.json file with your Open Library account details:
```json
{
    "credentials": {
        "username": "your_email@example.com",
        "password": "your_password"
    }
}
```

## 🚦 Running the Automation

To execute the full E2E flow and generate a visual HTML report:

```Bash
python3 run_tests.py
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

```markdown
🧩 Challenges & Solutions

    Asynchronous Flow Management: Leveraged Python's native asyncio and Playwright's async API to manage execution flow, avoiding the overhead of external testing frameworks while maintaining full control over the browser lifecycle

    Web Component Hydration: Open Library uses specialized Web Components that may take time to hydrate. The framework includes a "Smart Wait" mechanism that attempts to scrape the DOM as a fallback if hydration times out.

    Data Verification: Implemented a text normalization utility to handle curly quotes and special characters, ensuring robust assertions between search results and the reading list.
```

## 📝 License
This project is for educational and testing purposes.

## 📋 Requirements
* Python 3.9+
* Playwright 1.40+
* Open Library Account (for Login/List functionality)