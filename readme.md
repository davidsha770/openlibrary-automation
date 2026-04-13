# Open Library E2E Automation & Performance Suite

A high-performance End-to-End (E2E) testing framework for [Open Library](https://openlibrary.org). This project uses **Python**, **Playwright**, and **Asyncio** to automate user flows while benchmarking site performance.

## 🌟 Key Features

* **Asynchronous Architecture**: Built with `asyncio` for fast, non-blocking execution.
* **Page Object Model (POM)**: Organized into reusable and maintainable page classes.
* **Performance Tracking**: Captures real-time metrics (Load Time, DOM Content Loaded, First Paint) using the Browser Navigation Timing API.
* **Shadow DOM Handling**: Utilizes advanced recursive JavaScript injection to interact with complex Web Components.
* **Smart Library Sync**: Logic to detect current book status (Want to Read / Already Read) to avoid redundant actions.
* **Headless Execution**: Configured to run in the background for efficiency.

## 📁 Project Structure

```text
.
├── config/
│   └── config.json           # Credentials, test query, and performance thresholds
├── pages/
│   ├── base_page.py          # Core logic for performance measurement
│   ├── search_page.py        # Search and filtering functionality
│   ├── book_page.py          # Book-specific actions & JS injections
│   └── reading_list_page.py  # Reading list hydration and verification
├── tests/
│   └── test_e2e.py           # Main test orchestrator
├── utils/
│   └── logger_helper.py      # Custom logging configuration
├── outputs/
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

To execute the full E2E flow (Login -> Search -> Filter -> Add to List -> Verify):

```Bash
python3 -m tests.test_e2e
```

> **Note:** The script is currently configured to run in **Headless** mode.

## 📊 Performance Reporting

After each run, a detailed `performance_report.json` is generated in the `outputs/` folder. This includes:
* **Navigation Timing**: DNS lookup, DOM Content Loaded, and Full Load time.
* **Status**: Automatic "Pass/Fail" based on thresholds defined in `config.json`.

## 📸 Artifacts
* **Screenshots**: Automatically saved to `outputs/screenshots/` upon successful actions or verification steps.
* **Logs**: Comprehensive execution logs are streamed to the console for real-time monitoring.

## 📝 License
This project is for educational and testing purposes.