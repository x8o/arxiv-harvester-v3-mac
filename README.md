# arXiv Harvester v3

A Python application for harvesting, storing, and notifying about academic papers from arXiv.org, developed using rigorous Test-Driven Development (TDD) principles.

## Features

- **Search**: Query the arXiv API with customizable parameters (keywords, categories, date ranges)
- **Persistence**: Store paper metadata in a local SQLite database for efficient access
- **Notifications**: Send alerts about new papers to Slack via webhooks
- **Scheduling**: Automate regular harvesting of papers on daily, weekly, or monthly schedules
- **Filtering**: Identify and process only newly published papers

## Development Philosophy

This project strictly adheres to incremental Test-Driven Development with the following principles:

1. **Strict TDD Process**: Each feature is developed by first writing exactly 15 test cases, then implementing the minimal code to pass those tests
2. **Incremental Development**: Features are built in small, isolated units with comprehensive tests
3. **Minimal Unit Commits**: Development follows a "15 tests = 1 commit" rule for precise tracking with `git bisect`
4. **Continuous Integration**: Automated testing via GitHub Actions ensures code quality at every step
5. **Chain-of-Thought Development**: Every solution is thoroughly reasoned through before implementation

## Installation

```bash
# Clone the repository
git clone https://github.com/x8o/arxiv-harvester-v3-mac.git
cd arxiv-harvester-v3-mac

# Install package and dependencies
pip install -e .
```

## Quick Start

```python
# Basic usage example
from arxiv_harvester.api.client import ArxivApiClient
from arxiv_harvester.store.database import DatabaseManager
from arxiv_harvester.notify.slack import SlackNotifier
from arxiv_harvester.scheduler.scheduler import Scheduler

# Initialize components
api_client = ArxivApiClient()
db_manager = DatabaseManager("papers.db")
db_manager.initialize_database()
notifier = SlackNotifier()

# Configure and run a harvesting job
scheduler = Scheduler(api_client, db_manager, notifier)
scheduler.set_search_parameters(
    query="quantum computing",
    categories=["quant-ph", "cs.AI"],
    max_results=50
)
scheduler.set_slack_webhook("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
scheduler.run_harvest()
```

## Command Line Usage

The harvester can also be run as a command-line tool:

```bash
# Run with default settings (loads from state file if available)
python -m arxiv_harvester.run

# Specify search parameters
python -m arxiv_harvester.run --query "machine learning" --categories cs.AI,cs.LG --max-results 100

# Force run regardless of schedule
python -m arxiv_harvester.run --force-run
```

## Project Structure

```
arxiv-harvester-v3/
├── src/
│   └── arxiv_harvester/
│       ├── __init__.py
│       ├── api/               # API communication module
│       │   ├── __init__.py
│       │   └── client.py      # ArxivApiClient implementation
│       ├── store/             # Database storage module
│       │   ├── __init__.py
│       │   └── database.py    # DatabaseManager implementation
│       ├── notify/            # Notification module
│       │   ├── __init__.py
│       │   └── slack.py       # SlackNotifier implementation
│       └── scheduler/         # Scheduling module
│           ├── __init__.py
│           └── scheduler.py   # Scheduler implementation
├── tests/                     # Comprehensive test suite (60 tests)
│   ├── __init__.py
│   ├── test_arxiv_api_client.py  # 15 tests for API client
│   ├── test_store.py             # 15 tests for database management
│   ├── test_notify.py            # 15 tests for notifications
│   └── test_scheduler.py         # 15 tests for scheduling
├── .github/
│   └── workflows/             # CI/CD configuration
│       └── python-tests.yml    # GitHub Actions workflow
├── requirements.txt           # Project dependencies
└── setup.py                   # Package configuration
```

## Module Details

### API Client (ArxivApiClient)

Handles communication with the arXiv API, including searching for papers and managing rate limits.

```python
from arxiv_harvester.api.client import ArxivApiClient

client = ArxivApiClient()
papers = client.search(query="quantum computing", category="quant-ph", max_results=10)
print(f"Found {len(papers)} papers")
```

### Database Manager (DatabaseManager)

Manages the storage and retrieval of paper data using SQLite.

```python
from arxiv_harvester.store.database import DatabaseManager

db = DatabaseManager("papers.db")
db.initialize_database()
db.store_papers(papers)  # Store papers from API
recent_papers = db.get_recent_papers(5)  # Get 5 most recent papers
```

### Slack Notifier (SlackNotifier)

Sends notifications about new papers to Slack channels.

```python
from arxiv_harvester.notify.slack import SlackNotifier

notifier = SlackNotifier()
notifier.set_important_categories(["cs.AI", "quant-ph"])  # Highlight these categories
notifier.post_papers_to_slack(papers, "https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
```

### Scheduler

Coordinates the harvesting process according to defined schedules.

```python
from arxiv_harvester.scheduler.scheduler import Scheduler

scheduler = Scheduler(api_client, db_manager, notifier)
scheduler.set_schedule("weekly")  # Run once per week
scheduler.set_state_file("state.json")  # Save progress between runs
scheduler.run_harvest()
```

## Contributing

Contributions are welcome! This project strictly follows TDD principles, so please:

1. Write exactly 15 tests for any new feature or module
2. Ensure all tests pass before submitting a PR
3. Follow the minimal unit commit pattern (`15 tests = 1 commit`)

## License

MIT
