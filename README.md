# TruthCheck: Smart News Truth Checker

TruthCheck is a Python desktop application for analysing news credibility risk. It fetches news articles, searches fact-checking sites, applies NLP-based sentiment analysis, detects sensational keywords, calculates a 0 to 100 credibility score, and displays the results in a Tkinter dashboard with charts.
## Dashboard Preview

![TruthCheck Dashboard](assets/screenshots/truthcheck-dashboard.png)
> Important: TruthCheck does not decide whether something is absolutely true or false. It gives assistive credibility indicators based on limited signals.

## Key Features

- Live article fetching through NewsAPI
- Offline demo mode when no API key is available
- BeautifulSoup scraping from Snopes and PolitiFact search pages
- VADER sentiment scoring
- Sensational keyword risk detection
- 0 to 100 credibility score
- Colour-ready verdict categories: Likely credible, Needs review, High risk
- Tkinter GUI dashboard with article table, explanations, fact-check matches, and Matplotlib chart
- Object-oriented design using multiple classes
- Unit tests using Python's built-in `unittest`

## Project Structure

```text
TruthCheck/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── LICENSE
├── docs/
│   └── brief_report_template.md
├── tests/
│   ├── test_api_fetcher.py
│   ├── test_data_processor.py
│   └── test_scorer.py
└── truthcheck/
    ├── __init__.py
    ├── api_fetcher.py
    ├── config.py
    ├── dashboard.py
    ├── data_processor.py
    ├── models.py
    ├── scorer.py
    └── scrapers.py
```

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/TruthCheck.git
cd TruthCheck
```

### 2. Create and activate a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your NewsAPI key

Copy `.env.example` to `.env`:

Windows:

```bash
copy .env.example .env
```

macOS or Linux:

```bash
cp .env.example .env
```

Then edit `.env`:

```text
NEWS_API_KEY=your_real_key_here
```

Do not upload `.env` to GitHub.

## Running the App

Run the GUI:

```bash
python main.py
```

Run the terminal demo:

```bash
python main.py --cli --query "artificial intelligence"
```

## Running Tests

```bash
python -m unittest discover -s tests
```

## How the Score Works

The credibility score is calculated from four components:

1. Source trust score
2. Sensational keyword score
3. Sentiment intensity score
4. Fact-check match score

The score is intentionally simple and explainable, which makes it suitable for a programming assignment and video demonstration. It should not be presented as a production-grade misinformation detector.

## Ethical Notes

- The app uses polite request delays for scraping.
- It includes a clear disclaimer in the interface.
- It does not collect or store user data.
- It avoids presenting automated scores as final truth judgments.

