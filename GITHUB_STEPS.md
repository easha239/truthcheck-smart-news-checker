# GitHub Upload Guide for TruthCheck

## Option A: Upload with GitHub Desktop

1. Open GitHub Desktop.
2. Choose **File > Add local repository**.
3. Select the `TruthCheck` folder.
4. If GitHub Desktop asks to create a repository, click **Create a repository**.
5. Repository name: `TruthCheck`.
6. Description: `A Python desktop app for smart news credibility analysis.`
7. Keep the repository public if you want to showcase it in your resume.
8. Click **Publish repository**.

## Option B: Upload with Command Line

```bash
cd TruthCheck
git init
git add .
git commit -m "Initial TruthCheck project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/TruthCheck.git
git push -u origin main
```

## Before Pushing

Run these commands:

```bash
python -m unittest discover -s tests
python main.py --cli --query "artificial intelligence"
```

Check that `.env` is not included. Only `.env.example` should be uploaded.

## Suggested GitHub Description

TruthCheck is a Python Tkinter desktop application that fetches news articles, searches fact-checking sites, applies sentiment analysis and keyword risk detection, and generates an explainable credibility score.

## Suggested GitHub Topics

```text
python tkinter newsapi beautifulsoup misinformation-detection vader-sentiment data-visualization oop-project
```
