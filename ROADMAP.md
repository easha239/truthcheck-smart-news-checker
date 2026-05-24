# TruthCheck Development Roadmap

## Completed in Starter Version

- Project folder structure
- NewsAPI integration class with demo fallback
- Article dataclass
- Abstract scraper class
- Snopes scraper
- PolitiFact scraper
- Credibility scoring engine
- Data processing class
- Tkinter dashboard
- Matplotlib chart integration
- CLI demo mode
- Unit tests
- README and GitHub setup files

## Next Improvements

### Priority 1: Make the Demo Stronger

- Add a screenshot of the running GUI to the README.
- Record a short video showing the full search and scoring flow.
- Test with multiple search terms, such as `climate change`, `artificial intelligence`, and `public health`.

### Priority 2: Improve Fact-Check Matching

- Use better text similarity methods.
- Compare article headlines with fact-check titles and snippets.
- Add a minimum confidence threshold before showing fact-check matches.

### Priority 3: Improve the Interface

- Add export to CSV.
- Add a source filter.
- Add a button to open article URLs in the browser.
- Improve the keyword heatmap display.

### Priority 4: Make It More Research-Oriented

- Add a clear methodology section.
- Add limitations in the README.
- Add a small evaluation using example headlines.
