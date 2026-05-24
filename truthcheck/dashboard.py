"""Tkinter user interface for TruthCheck."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .api_fetcher import APIFetcher
from .config import load_config
from .data_processor import DataProcessor
from .models import Article, FactCheckResult
from .scorer import CredibilityScorer
from .scrapers import PolitiFactScraper, SnopesScraper, WebScraper


class Dashboard:
    """Main Tkinter application controller."""

    def __init__(self) -> None:
        self.config = load_config()
        self.fetcher = APIFetcher(self.config)
        self.processor = DataProcessor()
        self.scorer = CredibilityScorer()
        self.scraper = WebScraper([
            SnopesScraper(self.config),
            PolitiFactScraper(self.config),
        ])
        self.articles: list[Article] = []
        self.fact_checks: list[FactCheckResult] = []

        self.root = tk.Tk()
        self.root.title("TruthCheck | Smart News Truth Checker")
        self.root.geometry("1180x720")
        self.root.minsize(1000, 640)

        self._build_layout()

    def run(self) -> None:
        """Start the GUI event loop."""

        self.root.mainloop()

    def _build_layout(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=12)
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text="TruthCheck", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar(value="artificial intelligence")
        search_entry = ttk.Entry(header, textvariable=self.search_var, font=("Segoe UI", 12))
        search_entry.grid(row=0, column=1, sticky="ew", padx=12)
        ttk.Button(header, text="Search and Analyse", command=self._start_analysis).grid(row=0, column=2)

        self.status_var = tk.StringVar(value="Ready. Add NEWS_API_KEY in .env for live NewsAPI results. Demo mode works without a key.")
        ttk.Label(self.root, textvariable=self.status_var, padding=(12, 0)).grid(row=2, column=0, columnspan=3, sticky="ew")

        sidebar = ttk.Frame(self.root, padding=12)
        sidebar.grid(row=1, column=0, sticky="nsw")
        ttk.Label(sidebar, text="Project Signals", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
        self.summary_text = tk.Text(sidebar, width=30, height=18, wrap="word")
        self.summary_text.pack(fill="both", expand=True)
        self.summary_text.insert("end", "No analysis yet.\n")
        self.summary_text.configure(state="disabled")

        centre = ttk.Frame(self.root, padding=12)
        centre.grid(row=1, column=1, sticky="nsew")
        centre.rowconfigure(1, weight=1)
        centre.columnconfigure(0, weight=1)
        ttk.Label(centre, text="Article Analysis", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")
        columns = ("score", "verdict", "source", "title")
        self.article_table = ttk.Treeview(centre, columns=columns, show="headings", height=12)
        for col in columns:
            self.article_table.heading(col, text=col.title())
        self.article_table.column("score", width=70, anchor="center")
        self.article_table.column("verdict", width=120, anchor="center")
        self.article_table.column("source", width=140, anchor="w")
        self.article_table.column("title", width=450, anchor="w")
        self.article_table.grid(row=1, column=0, sticky="nsew", pady=8)
        self.article_table.bind("<<TreeviewSelect>>", self._show_selected_article)

        self.detail_text = tk.Text(centre, height=10, wrap="word")
        self.detail_text.grid(row=2, column=0, sticky="ew")
        self.detail_text.configure(state="disabled")

        right = ttk.Frame(self.root, padding=12)
        right.grid(row=1, column=2, sticky="nse")
        ttk.Label(right, text="Fact Checks and Chart", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        self.fact_text = tk.Text(right, width=38, height=16, wrap="word")
        self.fact_text.pack(fill="both", expand=True, pady=8)
        self.fact_text.configure(state="disabled")

        self.chart_frame = ttk.Frame(right)
        self.chart_frame.pack(fill="both", expand=True)
        self._draw_chart({"No results": 1})

        footer = ttk.Label(
            self.root,
            text="Disclaimer: TruthCheck provides assistive credibility indicators, not definitive verdicts.",
            padding=(12, 6),
        )
        footer.grid(row=3, column=0, columnspan=3, sticky="ew")

    def _start_analysis(self) -> None:
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Missing topic", "Please enter a headline or topic.")
            return
        self.status_var.set("Analysing. The interface may use demo data if live services are unavailable.")
        threading.Thread(target=self._run_analysis, args=(query,), daemon=True).start()

    def _run_analysis(self, query: str) -> None:
        articles = self.fetcher.fetch_articles(query, page_size=10)
        articles = self.processor.deduplicate(articles)
        fact_checks = self.scraper.search_fact_checks(query, limit_per_site=2)
        scored = self.scorer.score_articles(articles, fact_checks)
        self.root.after(0, lambda: self._render_results(scored, fact_checks))

    def _render_results(self, articles: list[Article], fact_checks: list[FactCheckResult]) -> None:
        self.articles = articles
        self.fact_checks = fact_checks
        for row in self.article_table.get_children():
            self.article_table.delete(row)
        for index, article in enumerate(articles):
            self.article_table.insert(
                "",
                "end",
                iid=str(index),
                values=(article.credibility_score, article.verdict, article.source, article.title),
            )
        self._update_summary()
        self._update_fact_checks()
        self._draw_chart(self.processor.source_distribution(articles))
        self.status_var.set(f"Analysis complete. {len(articles)} article(s), {len(fact_checks)} fact-check match(es).")
        if articles:
            self.article_table.selection_set("0")
            self._show_selected_article()

    def _update_summary(self) -> None:
        total = len(self.articles)
        avg = round(sum(article.credibility_score for article in self.articles) / total, 1) if total else 0
        high_risk = sum(1 for article in self.articles if article.verdict == "High risk")
        likely = sum(1 for article in self.articles if article.verdict == "Likely credible")
        text = (
            f"Articles analysed: {total}\n"
            f"Average score: {avg}\n"
            f"Likely credible: {likely}\n"
            f"High risk: {high_risk}\n\n"
            "Main scoring inputs:\n"
            "1. Source trust\n"
            "2. Sensational keywords\n"
            "3. Sentiment intensity\n"
            "4. Fact-check matches\n"
        )
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("end", text)
        self.summary_text.configure(state="disabled")

    def _update_fact_checks(self) -> None:
        self.fact_text.configure(state="normal")
        self.fact_text.delete("1.0", "end")
        if not self.fact_checks:
            self.fact_text.insert("end", "No fact-check search results found. This does not mean the claim is true.\n")
        else:
            for result in self.fact_checks:
                self.fact_text.insert("end", f"[{result.site}] {result.verdict}\n{result.title}\n{result.url}\n\n")
        self.fact_text.configure(state="disabled")

    def _show_selected_article(self, event=None) -> None:
        selected = self.article_table.selection()
        if not selected:
            return
        article = self.articles[int(selected[0])]
        details = [
            f"Title: {article.title}",
            f"Source: {article.source}",
            f"Date: {article.display_date}",
            f"URL: {article.url}",
            "",
            "Explanation:",
        ]
        details.extend(f"- {note}" for note in article.explanation)
        if article.keyword_risks:
            details.append("")
            details.append("Keyword heatmap weights:")
            details.extend(f"- {word}: {weight}" for word, weight in article.keyword_risks.items())
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("end", "\n".join(details))
        self.detail_text.configure(state="disabled")

    def _draw_chart(self, distribution: dict[str, int]) -> None:
        for child in self.chart_frame.winfo_children():
            child.destroy()
        figure = Figure(figsize=(3.2, 2.4), dpi=100)
        axis = figure.add_subplot(111)
        axis.pie(distribution.values(), labels=distribution.keys(), autopct="%1.0f%%")
        axis.set_title("Verdict Distribution")
        canvas = FigureCanvasTkAgg(figure, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
