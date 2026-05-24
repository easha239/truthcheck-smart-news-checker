# TruthCheck Brief Report

## 1. Project Aim
TruthCheck is a Python desktop application that helps users evaluate the credibility risk of news headlines and articles. It combines live news retrieval, fact-check search scraping, sentiment analysis, keyword risk detection, and visual summaries inside a Tkinter dashboard.

## 2. Design Decisions
The project uses an object-oriented structure because the application has clear service roles. `APIFetcher` manages live article retrieval, `Scraper` defines a reusable interface for fact-checking websites, `CredibilityScorer` handles the scoring algorithm, `DataProcessor` cleans and summarises the data, and `Dashboard` controls the user interface. This separation makes the code easier to test, extend, and explain in a video demonstration.

## 3. Data Sources
The live news component uses NewsAPI when an API key is available. If no key is present, the application switches to demo data so the interface and scoring pipeline can still be tested. Fact-checking signals are collected from Snopes and PolitiFact search results using polite BeautifulSoup scraping.

## 4. Scoring Method
The credibility score is not a final truth verdict. It is an assistive risk score based on four signals: source trust, sensational keyword use, sentiment intensity, and fact-check search matches. This design is intentionally cautious because misinformation detection is complex and cannot be solved reliably by simple keyword matching alone.

## 5. Challenges
The biggest challenge is that live websites and APIs can fail, change structure, or limit requests. To handle this, the project includes error handling, demo fallback data, and unit tests for the core logic. Another challenge is avoiding overclaiming. The application therefore displays a disclaimer and explains the score components to the user.

## 6. Future Improvements
Future versions could add a stronger claim-matching model, source transparency notes, multilingual support, browser integration, and a more reliable fact-check API. A better machine learning approach would require a labelled dataset and careful validation.
