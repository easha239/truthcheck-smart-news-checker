"""Modern CustomTkinter dashboard for TruthCheck."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .api_fetcher import APIFetcher
from .config import load_config
from .data_processor import DataProcessor
from .models import Article, FactCheckResult
from .scorer import CredibilityScorer
from .scrapers import PolitiFactScraper, SnopesScraper, WebScraper


APP_BG = "#07111f"
SIDEBAR_BG = "#081421"
CARD_BG = "#0d1b2a"
CARD_BG_2 = "#0b1626"
BORDER = "#1d2d44"
ACCENT = "#2f6bff"
ACCENT_HOVER = "#2558d8"
TEXT_PRIMARY = "#f5f7fb"
TEXT_SECONDARY = "#a9b4c2"
SUCCESS = "#43c463"
WARNING = "#f5b52e"
DANGER = "#ef5350"
MUTED = "#637083"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class Dashboard:
    """Main CustomTkinter application controller."""

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
        self.chart_canvas = None

        self.root = ctk.CTk()
        self.root.title("TruthLens | Smart News Truth Checker")
        self.root.geometry("1500x900")
        self.root.minsize(1250, 780)
        self.root.configure(fg_color=APP_BG)

        self.search_var = tk.StringVar(value="artificial intelligence")
        self.status_var = tk.StringVar(
            value="Ready. Add NEWS_API_KEY in .env for live NewsAPI results."
        )

        self._configure_styles()
        self._build_layout()

    def run(self) -> None:
        """Start GUI loop."""
        self.root.mainloop()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=CARD_BG_2,
            fieldbackground=CARD_BG_2,
            foreground=TEXT_PRIMARY,
            rowheight=32,
            bordercolor=BORDER,
            borderwidth=0,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Treeview.Heading",
            background=CARD_BG,
            foreground=TEXT_SECONDARY,
            bordercolor=BORDER,
            font=("Segoe UI", 10, "bold"),
        )

        style.map(
            "Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", TEXT_PRIMARY)],
        )

    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(0, minsize=250)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self._build_footer()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self.root,
            width=250,
            corner_radius=0,
            fg_color=SIDEBAR_BG,
        )
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="TruthLens",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=18, pady=(22, 0))

        ctk.CTkLabel(
            sidebar,
            text="Smart News Truth Checker",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=18, pady=(0, 28))

        menu_items = [
            "Dashboard",
            "News Analyzer",
            "Fact Checks",
            "Sources",
            "Saved Articles",
            "Alerts",
            "Settings",
        ]

        for index, item in enumerate(menu_items):
            button = ctk.CTkButton(
                sidebar,
                text=item,
                height=44,
                corner_radius=12,
                fg_color=ACCENT if index == 0 else "transparent",
                hover_color=ACCENT_HOVER,
                text_color=TEXT_PRIMARY,
                anchor="w",
                font=ctk.CTkFont(size=15),
            )
            button.pack(fill="x", padx=16, pady=5)

        ctk.CTkFrame(sidebar, fg_color="transparent", height=70).pack(fill="x")

        summary_card = ctk.CTkFrame(
            sidebar,
            fg_color=CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
        )
        summary_card.pack(fill="x", padx=16, pady=(8, 14))
        summary_card.configure(height=155)
        summary_card.pack_propagate(False)

        ctk.CTkLabel(
            summary_card,
            text="Daily Scan Summary",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self.sidebar_summary = ctk.CTkLabel(
            summary_card,
            text="Articles: 0\nAvg Score: 0\nCredible: 0\nReview: 0\nHigh Risk: 0",
            justify="left",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        )
        self.sidebar_summary.pack(anchor="w", padx=14, pady=(0, 14))

        dark_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        dark_row.pack(fill="x", padx=18, pady=(0, 22))

        ctk.CTkLabel(
            dark_row,
            text="Dark Mode",
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        dark_switch = ctk.CTkSwitch(dark_row, text="")
        dark_switch.select()
        dark_switch.pack(side="right")

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self._build_topbar(main)
        self._build_center_area(main)
        self._build_right_area(main)

    def _build_topbar(self, parent: ctk.CTkFrame) -> None:
        topbar = ctk.CTkFrame(parent, fg_color="transparent")
        topbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        topbar.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            topbar,
            textvariable=self.search_var,
            placeholder_text="Enter a news topic, headline or paste URL...",
            height=54,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            fg_color=CARD_BG,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=16),
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda _event: self._start_analysis())

        self.analyze_button = ctk.CTkButton(
            topbar,
            text="Analyze",
            width=135,
            height=54,
            corner_radius=14,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start_analysis,
        )
        self.analyze_button.grid(row=0, column=1)

    def _build_center_area(self, parent: ctk.CTkFrame) -> None:
        center = ctk.CTkFrame(parent, fg_color="transparent")
        center.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(0, weight=0)
        center.grid_rowconfigure(1, weight=0)
        center.grid_rowconfigure(2, weight=5)

        self._build_analysis_card(center)
        self._build_fact_card(center)
        self._build_articles_card(center)

    def _build_analysis_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(0, weight=2)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="Analysis Report",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=26, pady=(18, 8))

        self.updated_label = ctk.CTkLabel(
            card,
            text="Not analyzed yet",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
        )
        self.updated_label.grid(row=0, column=1, sticky="e", padx=22, pady=(18, 8))

        self.headline_label = ctk.CTkLabel(
            card,
            text="No article selected yet",
            justify="left",
            wraplength=620,
            font=ctk.CTkFont(size=23, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.headline_label.grid(row=1, column=0, sticky="w", padx=26, pady=(8, 8))

        self.meta_label = ctk.CTkLabel(
            card,
            text="Search a topic to begin",
            font=ctk.CTkFont(size=15),
            text_color=TEXT_SECONDARY,
        )
        self.meta_label.grid(row=2, column=0, sticky="w", padx=26, pady=(0, 22))

        score_card = ctk.CTkFrame(
            card,
            fg_color=CARD_BG_2,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        score_card.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=18, pady=18)

        ctk.CTkLabel(
            score_card,
            text="Credibility Score",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(pady=(18, 8))

        self.score_value = ctk.CTkLabel(
            score_card,
            text="0 / 100",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color=TEXT_SECONDARY,
        )
        self.score_value.pack(pady=4)

        self.score_verdict = ctk.CTkLabel(
            score_card,
            text="Not analyzed",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_SECONDARY,
        )
        self.score_verdict.pack(pady=4)

        self.score_desc = ctk.CTkLabel(
            score_card,
            text="Run an analysis to see the result.",
            wraplength=210,
            justify="center",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
        )
        self.score_desc.pack(padx=14, pady=(4, 18))

    def _build_fact_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Fact-check Results",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 8))

        self.fact_text = ctk.CTkTextbox(
            card,
            height=85,
            corner_radius=12,
            fg_color=CARD_BG_2,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=12),
            wrap="word",
        )
        self.fact_text.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 14))
        self._set_text(self.fact_text, "Fact-check matches will appear here.")

    def _build_articles_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=2, column=0, sticky="nsew", pady=(0, 0))
        card.configure(height=390)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 6))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Article Results",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        self.article_count_label = ctk.CTkLabel(
            header,
            text="0 articles",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=13),
        )
        self.article_count_label.grid(row=0, column=1, sticky="e")

        table_frame = ctk.CTkFrame(
            card,
            fg_color=CARD_BG_2,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 14))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("score", "verdict", "source", "title")
        self.article_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=10,
        )

        self.article_table.heading("score", text="Score")
        self.article_table.heading("verdict", text="Verdict")
        self.article_table.heading("source", text="Source")
        self.article_table.heading("title", text="Title")

        self.article_table.column("score", width=70, anchor="center", stretch=False)
        self.article_table.column("verdict", width=130, anchor="center", stretch=False)
        self.article_table.column("source", width=160, anchor="w", stretch=False)
        self.article_table.column("title", width=560, anchor="w", stretch=True)

        self.article_table.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        self.article_table.bind("<<TreeviewSelect>>", self._show_selected_article)

        scrollbar = ctk.CTkScrollbar(table_frame, command=self.article_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(4, 8), pady=8)
        self.article_table.configure(yscrollcommand=scrollbar.set)

    def _build_right_area(self, parent: ctk.CTkFrame) -> None:
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self._build_source_card(right)
        self._build_reason_card(right)

    def _build_source_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Verdict Breakdown",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 8))

        self.chart_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.chart_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=4)

        self.chart_legend = ctk.CTkLabel(
            card,
            text="No results yet",
            justify="left",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=13),
        )
        self.chart_legend.grid(row=2, column=0, sticky="w", padx=22, pady=(4, 18))

        self._draw_chart({"No results": 1})

    def _build_reason_card(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="Reasoning Signals",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 8))

        self.reason_box = ctk.CTkTextbox(
            card,
            corner_radius=12,
            fg_color=CARD_BG_2,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=12),
            wrap="word",
        )
        self.reason_box.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 20))
        self._set_text(self.reason_box, "Analysis reasons will appear here after you run a search.")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self.root, fg_color=APP_BG, height=34)
        footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 8))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer,
            text="TruthLens uses AI and multiple verification methods. Results are assistive indicators, not definitive verdicts.",
            text_color=MUTED,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            footer,
            textvariable=self.status_var,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=1, sticky="e")

    def _start_analysis(self) -> None:
        query = self.search_var.get().strip()

        if not query:
            messagebox.showwarning("Missing topic", "Please enter a headline, URL, or topic.")
            return

        self.status_var.set("Analysing live sources...")
        self.analyze_button.configure(state="disabled", text="Analyzing...")

        threading.Thread(
            target=self._run_analysis,
            args=(query,),
            daemon=True,
        ).start()

    def _run_analysis(self, query: str) -> None:
        try:
            articles = self.fetcher.fetch_articles(query, page_size=10)
            articles = self.processor.deduplicate(articles)
            fact_checks = self.scraper.search_fact_checks(query, limit_per_site=2)
            scored = self.scorer.score_articles(articles, fact_checks)

            self.root.after(0, lambda: self._render_results(scored, fact_checks))

        except Exception as exc:
            self.root.after(0, lambda: self._show_error(exc))

    def _show_error(self, exc: Exception) -> None:
        self.status_var.set("Analysis failed. Check the terminal for details.")
        self.analyze_button.configure(state="normal", text="Analyze")
        messagebox.showerror("Analysis failed", str(exc))

    def _render_results(
        self,
        articles: list[Article],
        fact_checks: list[FactCheckResult],
    ) -> None:
        self.articles = articles
        self.fact_checks = fact_checks

        for row in self.article_table.get_children():
            self.article_table.delete(row)

        for index, article in enumerate(articles):
            self.article_table.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    article.credibility_score,
                    article.verdict,
                    article.source,
                    article.title,
                ),
            )

        self.article_count_label.configure(text=f"{len(articles)} articles")
        self._update_sidebar_summary()
        self._update_fact_checks()
        self._draw_chart(self.processor.source_distribution(articles))

        self.status_var.set(
            f"Analysis complete. {len(articles)} article(s), {len(fact_checks)} fact-check match(es)."
        )
        self.analyze_button.configure(state="normal", text="Analyze")
        self.updated_label.configure(text="Analyzed just now")

        if articles:
            self.article_table.selection_set("0")
            self.article_table.focus("0")
            self._show_selected_article()
        else:
            self.headline_label.configure(text="No articles found")
            self.meta_label.configure(text="Try a different topic or check your API key.")
            self.score_value.configure(text="0 / 100", text_color=TEXT_SECONDARY)
            self.score_verdict.configure(text="No result", text_color=TEXT_SECONDARY)
            self.score_desc.configure(text="No score is available.")
            self._set_text(self.reason_box, "No articles were returned for this query.")

    def _update_sidebar_summary(self) -> None:
        total = len(self.articles)

        credible = sum(
            1 for article in self.articles
            if article.verdict == "Likely credible"
        )
        review = sum(
            1 for article in self.articles
            if article.verdict == "Needs review"
        )
        high_risk = sum(
            1 for article in self.articles
            if article.verdict == "High risk"
        )

        avg = (
            round(sum(article.credibility_score for article in self.articles) / total, 1)
            if total else 0
        )

        text = (
            f"Articles: {total}\n"
            f"Avg Score: {avg}\n"
            f"Credible: {credible}\n"
            f"Review: {review}\n"
            f"High Risk: {high_risk}"
        )

        self.sidebar_summary.configure(text=text)

    def _update_fact_checks(self) -> None:
        if not self.fact_checks:
            self._set_text(
                self.fact_text,
                "No close fact-check search results found.\n\nThis does not mean the claim is true. It only means the app did not find a closely matching fact-check result.",
            )
            return

        lines = []

        for result in self.fact_checks:
            lines.append(f"{result.site}  |  {result.verdict}")
            lines.append(result.title)
            lines.append(result.url)

            if result.snippet:
                lines.append(result.snippet)

            lines.append("")

        self._set_text(self.fact_text, "\n".join(lines))

    def _show_selected_article(self, event=None) -> None:
        selected = self.article_table.selection()

        if not selected:
            return

        article = self.articles[int(selected[0])]
        color = self._verdict_color(article.verdict, article.credibility_score)

        self.headline_label.configure(text=f"“{article.title}”")
        self.meta_label.configure(text=f"{article.source}  |  {article.display_date}")
        self.score_value.configure(text=f"{article.credibility_score} / 100", text_color=color)
        self.score_verdict.configure(text=article.verdict, text_color=color)
        self.score_desc.configure(text=self._score_description(article.verdict))

        details = []

        if article.explanation:
            details.extend(f"• {note}" for note in article.explanation)
        else:
            details.append("• No detailed explanation was generated for this article.")

        details.append("")
        details.append(f"URL: {article.url}")

        if article.keyword_risks:
            details.append("")
            details.append("Keyword risk weights:")
            details.extend(
                f"• {word}: {weight}"
                for word, weight in article.keyword_risks.items()
            )

        self._set_text(self.reason_box, "\n".join(details))

    def _draw_chart(self, distribution: dict[str, int]) -> None:
        for child in self.chart_frame.winfo_children():
            child.destroy()

        labels = list(distribution.keys())
        values = list(distribution.values())

        colors = [self._chart_color(label) for label in labels]

        figure = Figure(figsize=(3.6, 2.8), dpi=100, facecolor=CARD_BG)
        axis = figure.add_subplot(111)
        axis.set_facecolor(CARD_BG)

        axis.pie(
            values,
            labels=None,
            autopct="%1.0f%%",
            startangle=90,
            colors=colors,
            textprops={"color": TEXT_PRIMARY, "fontsize": 10},
            wedgeprops={"width": 0.38, "edgecolor": CARD_BG},
        )

        axis.text(
            0,
            0,
            str(sum(values)),
            ha="center",
            va="center",
            color=TEXT_PRIMARY,
            fontsize=20,
            weight="bold",
        )

        axis.set_aspect("equal")

        canvas = FigureCanvasTkAgg(figure, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.chart_canvas = canvas

        legend_lines = [
            f"{label}: {value}"
            for label, value in distribution.items()
        ]
        self.chart_legend.configure(text="\n".join(legend_lines))

    def _set_text(self, textbox: ctk.CTkTextbox, value: str) -> None:
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", value)
        textbox.configure(state="disabled")

    @staticmethod
    def _verdict_color(verdict: str, score: int) -> str:
        if verdict == "Likely credible" or score >= 75:
            return SUCCESS
        if verdict == "High risk" or score < 55:
            return DANGER
        return WARNING

    @staticmethod
    def _chart_color(label: str) -> str:
        mapping = {
            "Likely credible": SUCCESS,
            "Needs review": WARNING,
            "High risk": DANGER,
            "No results": MUTED,
        }
        return mapping.get(label, ACCENT)

    @staticmethod
    def _score_description(verdict: str) -> str:
        if verdict == "Likely credible":
            return "This article appears stronger, but still verify the original source."
        if verdict == "High risk":
            return "This article has signals that require serious caution."
        return "This information should be approached with caution."