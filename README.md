# arXiv Harvester v3

A Python application for extracting, processing, and organizing academic papers from arXiv.org using TDD principles.

## Features

- Search arXiv API with various parameters (keywords, categories, date range)
- Download PDFs of papers
- Extract metadata from papers
- Store paper metadata and links in a local database
- Simple UI for searching and viewing downloaded papers

## Development Approach

This project follows Test-Driven Development (TDD) principles with a strict rule of 15 test cases per function. The development workflow consists of:

1. Write comprehensive test cases
2. Implement the minimal code to pass tests
3. Run tests to verify implementation
4. Refactor while maintaining test coverage

## Setup

```bash
# Clone the repository
git clone [repo-url]
cd arxiv-harvester-v3

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest
```

## Project Structure

```
arxiv-harvester-v3/
├── src/
│   └── arxiv_harvester/
│       ├── __init__.py
│       ├── api/
│       ├── data/
│       ├── models/
│       └── ui/
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_data.py
│   └── test_models.py
└── requirements.txt
```

## License

MIT
