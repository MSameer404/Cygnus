# src/app/ui/settings_page.py
"""Settings page with subject management, D-Day events, and data options."""

import csv
import os
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QSlider,
    QCheckBox,
)

from app.core import dday_manager, session_manager, subject_manager
from app.core.utils import CURRENT_VERSION
from app.data.database import DB_PATH
from app.data.models import DDayEvent, Subject
from app.data.settings_store import load_setting, save_setting
from app.ui.contact_dialog import ContactDialog
from app.ui.widgets.report_dialog import ReportDialog


class CollapsibleSection(QWidget):
    """A collapsible section with a toggle button and content area."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._is_expanded = False
        self._title = title
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toggle button
        self._toggle_btn = QPushButton(f"▶   {title}")
        self._toggle_btn.setProperty("class", "collapsible-btn")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_btn_style()
        self._toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self._toggle_btn)

        # Content container
        self._content = QWidget()
        self._content.setVisible(False)
        self._content.setStyleSheet(
            """
            QWidget {
                background-color: rgba(20, 8, 25, 0.22);
                border-left: 1px solid rgba(16, 185, 129, 0.14);
                border-right: 1px solid rgba(16, 185, 129, 0.14);
                border-bottom: 1px solid rgba(16, 185, 129, 0.14);
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
            """
        )
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(18, 16, 18, 18)
        self._content_layout.setSpacing(12)
        layout.addWidget(self._content)

    def _update_btn_style(self):
        border_radius_str = "border-radius: 12px;"
        if self._is_expanded:
            border_radius_str = "border-radius: 12px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; border-bottom: 1px solid rgba(16, 185, 129, 0.04);"
            
        self._toggle_btn.setStyleSheet(
            f"""
            QPushButton {{
                text-align: left;
                padding: 14px 20px;
                background-color: rgba(30, 10, 35, 0.45);
                border: 1px solid rgba(16, 185, 129, 0.14);
                {border_radius_str}
                color: #ECFDF5;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(16, 185, 129, 0.08);
                border-color: rgba(16, 185, 129, 0.45);
                color: #10B981;
            }}
            """
        )

    def _toggle(self):
        self._is_expanded = not self._is_expanded
        self._content.setVisible(self._is_expanded)
        self._update_btn_style()
        if self._is_expanded:
            self._toggle_btn.setText(f"▼   {self._title}")
        else:
            self._toggle_btn.setText(f"▶   {self._title}")

    def add_widget(self, widget):
        """Add a widget to the collapsible content area."""
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Add a layout to the collapsible content area."""
        self._content_layout.addLayout(layout)


class SettingsPage(QWidget):
    """Settings page: subject CRUD, D-Day management, data export/reset."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        from PySide6.QtWidgets import QStackedWidget
        
        # Main vertical layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ---------- Header Bar (consistent with other pages) ----------
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(16)

        title = QLabel("Settings")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)
        header_layout.addStretch()
        outer_layout.addWidget(header)

        # Horizontal separator line below header
        horizontal_line = QFrame()
        horizontal_line.setObjectName("headerSeparator")
        horizontal_line.setFrameShape(QFrame.Shape.HLine)
        horizontal_line.setFixedHeight(1)
        outer_layout.addWidget(horizontal_line)

        # ---------- Content Area with Splitter ----------
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ========== 1. LEFT SUB-SIDEBAR (Category Navigation List) ==========
        self._sub_sidebar = QWidget()
        self._sub_sidebar.setFixedWidth(220)
        sub_sidebar_layout = QVBoxLayout(self._sub_sidebar)
        sub_sidebar_layout.setContentsMargins(0, 0, 16, 0)
        sub_sidebar_layout.setSpacing(8)

        # Add category title
        sub_sidebar_title = QLabel("CATEGORIES")
        sub_sidebar_title.setStyleSheet("font-size: 11px; font-weight: bold; color: rgba(203, 170, 205, 0.5); letter-spacing: 1px; margin-bottom: 4px; padding-left: 8px;")
        sub_sidebar_layout.addWidget(sub_sidebar_title)

        # Category buttons setup
        self._nav_buttons = []
        categories = [
            ("📚   Subjects", 0),
            ("📅   D-Day Events", 1),
            ("⏰   Timer Settings", 2),
            ("🎨   Visuals & Theme", 3),
            ("📦   System & Data", 4),
            ("📖   Usage Guide", 5),
        ]
        
        for name, idx in categories:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(46)
            btn.clicked.connect(lambda checked=False, i=idx: self._switch_sub_page(i))
            sub_sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sub_sidebar_layout.addStretch()
        splitter.addWidget(self._sub_sidebar)

        # ========== 2. CENTER PANEL: Stacked Cards Container ==========
        self._stacked_card = QFrame()
        self._stacked_card.setProperty("class", "card")
        self._stacked_layout = QVBoxLayout(self._stacked_card)
        self._stacked_layout.setContentsMargins(24, 24, 24, 24)
        self._stacked_layout.setSpacing(16)

        self._stacked_widget = QStackedWidget()
        self._stacked_layout.addWidget(self._stacked_widget)
        splitter.addWidget(self._stacked_card)

        # ---------- Build Sub-Pages inside StackedWidget ----------

        # ------ Page 0: Subjects ------
        self._page_subjects = QWidget()
        subjects_layout = QVBoxLayout(self._page_subjects)
        subjects_layout.setContentsMargins(0, 0, 0, 0)
        subjects_layout.setSpacing(16)

        subj_title_lbl = QLabel("📚   Manage Subjects")
        subj_title_lbl.setProperty("class", "subheading")
        subjects_layout.addWidget(subj_title_lbl)

        subj_desc = QLabel("Create and customize your study subjects. Assign unique, color-coded glows to organize your stopwatch sessions.")
        subj_desc.setWordWrap(True)
        subj_desc.setStyleSheet("color: rgba(203, 170, 205, 0.7); font-size: 13px; line-height: 1.4;")
        subjects_layout.addWidget(subj_desc)

        subj_scroll = QScrollArea()
        subj_scroll.setWidgetResizable(True)
        subj_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self._subj_content = QWidget()
        self._subjects_container = QVBoxLayout(self._subj_content)
        self._subjects_container.setContentsMargins(0, 0, 8, 0)
        self._subjects_container.setSpacing(8)
        self._subjects_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        subj_scroll.setWidget(self._subj_content)
        subjects_layout.addWidget(subj_scroll, stretch=1)

        add_subj_row = QHBoxLayout()
        add_subject_btn = QPushButton("+   Add New Subject")
        add_subject_btn.setProperty("class", "secondary")
        add_subject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_subject_btn.clicked.connect(self._add_subject)
        add_subj_row.addWidget(add_subject_btn)
        add_subj_row.addStretch()
        subjects_layout.addLayout(add_subj_row)

        self._stacked_widget.addWidget(self._page_subjects)

        # ------ Page 1: D-Day Events ------
        self._page_dday = QWidget()
        dday_layout = QVBoxLayout(self._page_dday)
        dday_layout.setContentsMargins(0, 0, 0, 0)
        dday_layout.setSpacing(16)

        dday_title_lbl = QLabel("📅   D-Day Events")
        dday_title_lbl.setProperty("class", "subheading")
        dday_layout.addWidget(dday_title_lbl)

        dday_desc = QLabel("Track upcoming exams, deadlines, or milestones. Your D-Day events are displayed automatically on your dashboard.")
        dday_desc.setWordWrap(True)
        dday_desc.setStyleSheet("color: rgba(203, 170, 205, 0.7); font-size: 13px; line-height: 1.4;")
        dday_layout.addWidget(dday_desc)

        dday_scroll = QScrollArea()
        dday_scroll.setWidgetResizable(True)
        dday_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self._dday_content = QWidget()
        self._dday_container = QVBoxLayout(self._dday_content)
        self._dday_container.setContentsMargins(0, 0, 8, 0)
        self._dday_container.setSpacing(8)
        self._dday_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        dday_scroll.setWidget(self._dday_content)
        dday_layout.addWidget(dday_scroll, stretch=1)

        add_dday_row = QHBoxLayout()
        add_dday_btn = QPushButton("+   Add New Event")
        add_dday_btn.setProperty("class", "secondary")
        add_dday_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_dday_btn.clicked.connect(self._add_dday)
        add_dday_row.addWidget(add_dday_btn)
        add_dday_row.addStretch()
        dday_layout.addLayout(add_dday_row)

        self._stacked_widget.addWidget(self._page_dday)

        # ------ Page 2: Preferences ------
        self._page_timer = QWidget()
        timer_layout = QVBoxLayout(self._page_timer)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_layout.setSpacing(20)

        timer_title_lbl = QLabel("⏰   Timer & Navigation Preferences")
        timer_title_lbl.setProperty("class", "subheading")
        timer_layout.addWidget(timer_title_lbl)

        timer_desc = QLabel("Adjust timer styles and customise which trackers appear on your sidebar navigation menu.")
        timer_desc.setWordWrap(True)
        timer_desc.setStyleSheet("color: rgba(203, 170, 205, 0.7); font-size: 13px;")
        timer_layout.addWidget(timer_desc)

        pref_card = QFrame()
        pref_card.setProperty("class", "card")
        pref_card_layout = QVBoxLayout(pref_card)
        pref_card_layout.setContentsMargins(20, 20, 20, 20)
        pref_card_layout.setSpacing(14)

        lbl_timer = QLabel("Select Timer Mode:")
        lbl_timer.setStyleSheet("color: #ECFDF5; font-size: 14px; font-weight: bold;")
        pref_card_layout.addWidget(lbl_timer)

        self._timer_mode_combo = QComboBox()
        self._timer_mode_combo.addItem("Start from Zero (Standard)", "start_from_zero")
        self._timer_mode_combo.addItem("Daily Total Time (Accumulative)", "daily_total")
        self._timer_mode_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._timer_mode_combo.setFixedHeight(40)
        self._timer_mode_combo.setStyleSheet("""
            QComboBox {
                background: rgba(40, 15, 45, 0.55);
                border: 1px solid rgba(16, 185, 129, 0.15);
                border-radius: 8px;
                padding: 8px 12px;
                color: #ECFDF5;
                font-weight: 600;
            }
            QComboBox::drop-down { border: none; }
        """)

        current_timer_style = load_setting("timer_style", "start_from_zero")
        idx = self._timer_mode_combo.findData(current_timer_style)
        if idx >= 0:
            self._timer_mode_combo.setCurrentIndex(idx)

        self._timer_mode_combo.currentIndexChanged.connect(self._on_timer_style_changed)
        pref_card_layout.addWidget(self._timer_mode_combo)

        lbl_timer_desc = QLabel(
            "• <b>Start from Zero</b>: The timer resets to 00:00:00 every time you click start, showing the duration of the current session alone.\n\n"
            "• <b>Daily Total Time</b>: The timer automatically loads the total seconds you studied this subject today. Starting the timer increments directly from your daily accumulated total, so you always see your day's total focus progress."
        )
        lbl_timer_desc.setWordWrap(True)
        lbl_timer_desc.setStyleSheet("color: rgba(203, 170, 205, 0.75); font-size: 12px; line-height: 1.5;")
        pref_card_layout.addWidget(lbl_timer_desc)

        timer_layout.addWidget(pref_card)

        # Navigation preferences card
        nav_pref_card = QFrame()
        nav_pref_card.setProperty("class", "card")
        nav_pref_card_layout = QVBoxLayout(nav_pref_card)
        nav_pref_card_layout.setContentsMargins(20, 20, 20, 20)
        nav_pref_card_layout.setSpacing(14)

        lbl_nav = QLabel("Sidebar Navigation Customization:")
        lbl_nav.setStyleSheet("color: #FFD6E0; font-size: 14px; font-weight: bold;")
        nav_pref_card_layout.addWidget(lbl_nav)

        self._show_trackers_checkbox = QCheckBox("Show optional trackers (Syllabus & Test Tracker)")
        self._show_trackers_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_trackers_checkbox.setChecked(load_setting("show_optional_trackers", False))
        self._show_trackers_checkbox.setStyleSheet("""
            QCheckBox {
                color: #CBAACD;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self._show_trackers_checkbox.stateChanged.connect(self._on_show_trackers_changed)
        nav_pref_card_layout.addWidget(self._show_trackers_checkbox)

        lbl_nav_desc = QLabel(
            "Toggle this option to show or hide the optional Syllabus Tracker and Test Tracker pages from your primary sidebar menu. Settings is automatically kept at the very bottom."
        )
        lbl_nav_desc.setWordWrap(True)
        lbl_nav_desc.setStyleSheet("color: rgba(203, 170, 205, 0.75); font-size: 12px; line-height: 1.5;")
        nav_pref_card_layout.addWidget(lbl_nav_desc)

        timer_layout.addWidget(nav_pref_card)
        timer_layout.addStretch()

        self._stacked_widget.addWidget(self._page_timer)

        # ------ Page 3: Visuals & Theme ------
        self._page_appearance = QWidget()
        appearance_scroll = QScrollArea()
        appearance_scroll.setWidgetResizable(True)
        appearance_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        appearance_content = QWidget()
        appearance_layout = QVBoxLayout(appearance_content)
        appearance_layout.setContentsMargins(0, 0, 8, 0)
        appearance_layout.setSpacing(20)

        app_title_lbl = QLabel("🎨   Visuals & Theme")
        app_title_lbl.setProperty("class", "subheading")
        appearance_layout.addWidget(app_title_lbl)

        # Accent Theme Card
        theme_card = QFrame()
        theme_card.setProperty("class", "card")
        theme_card_layout = QVBoxLayout(theme_card)
        theme_card_layout.setContentsMargins(20, 20, 20, 20)
        theme_card_layout.setSpacing(14)

        theme_lbl = QLabel("Select Accent Theme:")
        theme_lbl.setStyleSheet("color: #ECFDF5; font-size: 14px; font-weight: bold;")
        theme_card_layout.addWidget(theme_lbl)

        from app.core.theme_manager import THEMES
        from PySide6.QtWidgets import QGridLayout
        
        current_theme = load_setting("current_theme", "Fox (Amber)")
        
        grid = QGridLayout()
        grid.setSpacing(12)
        
        self._theme_buttons = {}
        
        row, col = 0, 0
        for t_name, t_colors in THEMES.items():
            btn = QPushButton(f"●  {t_name}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(160, 44)
            
            accent = t_colors["accent"]
            is_active = (t_name == current_theme)
            border_color = accent if is_active else "#065F46"
            border_width = "2px" if is_active else "1px"
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(30, 10, 35, 0.45);
                    border: {border_width} solid {border_color};
                    border-radius: 10px;
                    color: {accent};
                    font-weight: 600;
                    text-align: left;
                    padding-left: 14px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    border-color: {accent};
                    background-color: rgba(16, 185, 129, 0.08);
                }}
            """)
            
            btn.clicked.connect(lambda checked=False, theme=t_name: self._change_theme(theme))
            self._theme_buttons[t_name] = btn
            grid.addWidget(btn, row, col)
            
            col += 1
            if col > 1:
                col = 0
                row += 1

        theme_card_layout.addLayout(grid)
        appearance_layout.addWidget(theme_card)

        # Custom Background Image Card
        bg_card = QFrame()
        bg_card.setProperty("class", "card")
        self._bg_container = QVBoxLayout(bg_card)
        self._bg_container.setSpacing(14)
        
        bg_header = QLabel("🖼️   Custom Background Image")
        bg_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #ECFDF5;")
        self._bg_container.addWidget(bg_header)
        
        from app.core import background_manager as bm
        self._build_bg_ui()
        appearance_layout.addWidget(bg_card)

        appearance_scroll.setWidget(appearance_content)
        
        appearance_layout_outer = QVBoxLayout(self._page_appearance)
        appearance_layout_outer.setContentsMargins(0, 0, 0, 0)
        appearance_layout_outer.addWidget(appearance_scroll)

        self._stacked_widget.addWidget(self._page_appearance)

        # ------ Page 4: System & Data ------
        self._page_data = QWidget()
        data_scroll = QScrollArea()
        data_scroll.setWidgetResizable(True)
        data_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        data_content = QWidget()
        data_layout = QVBoxLayout(data_content)
        data_layout.setContentsMargins(0, 0, 8, 0)
        data_layout.setSpacing(20)

        data_title_lbl = QLabel("📦   System & Data")
        data_title_lbl.setProperty("class", "subheading")
        data_layout.addWidget(data_title_lbl)

        # Database utilities card
        db_card = QFrame()
        db_card.setProperty("class", "card")
        db_card_layout = QVBoxLayout(db_card)
        db_card_layout.setContentsMargins(20, 20, 20, 20)
        db_card_layout.setSpacing(12)

        db_header = QLabel("Database Settings")
        db_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #ECFDF5;")
        db_card_layout.addWidget(db_header)

        db_info = QLabel(f"<b>Path:</b> {DB_PATH}")
        db_info.setStyleSheet("color: rgba(203, 170, 205, 0.85); font-size: 12px;")
        db_info.setWordWrap(True)
        db_card_layout.addWidget(db_info)

        data_btns = QHBoxLayout()
        data_btns.setSpacing(10)

        export_btn = QPushButton("📥   Export Study Log (.csv)")
        export_btn.setProperty("class", "secondary")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_csv)
        data_btns.addWidget(export_btn)

        reset_btn = QPushButton("🗑️   Reset All Data")
        reset_btn.setProperty("class", "danger-btn")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_data)
        data_btns.addWidget(reset_btn)

        data_btns.addStretch()
        db_card_layout.addLayout(data_btns)
        data_layout.addWidget(db_card)

        # About card
        about_card = QFrame()
        about_card.setProperty("class", "card")
        about_card_layout = QVBoxLayout(about_card)
        about_card_layout.setContentsMargins(20, 20, 20, 20)
        about_card_layout.setSpacing(12)

        about_header = QLabel(f"About Cygnus — v{CURRENT_VERSION}")
        about_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #ECFDF5;")
        about_card_layout.addWidget(about_header)

        about_desc = QLabel("Cygnus is a premium, glassmorphic Yeolpumta-inspired focus timer designed to optimize study tracking. Built with high-fidelity visuals, robust database logging, and responsive local charts.")
        about_desc.setWordWrap(True)
        about_desc.setStyleSheet("color: rgba(203, 170, 205, 0.8); font-size: 12px; line-height: 1.5;")
        about_card_layout.addWidget(about_desc)

        feedback_row = QHBoxLayout()
        feedback_row.setSpacing(10)

        contact_btn = QPushButton("📧   Contact Support")
        contact_btn.setProperty("class", "secondary")
        contact_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        contact_btn.clicked.connect(self._open_contact)
        feedback_row.addWidget(contact_btn)

        report_btn = QPushButton("💬   Send Feedback")
        report_btn.setProperty("class", "secondary")
        report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        report_btn.clicked.connect(self._open_report)
        feedback_row.addWidget(report_btn)

        feedback_row.addStretch()
        about_card_layout.addLayout(feedback_row)
        data_layout.addWidget(about_card)

        data_scroll.setWidget(data_content)
        
        data_layout_outer = QVBoxLayout(self._page_data)
        data_layout_outer.setContentsMargins(0, 0, 0, 0)
        data_layout_outer.addWidget(data_scroll)

        self._stacked_widget.addWidget(self._page_data)

        # ------ Page 5: Usage Guide ------
        self._page_guide = QWidget()
        guide_scroll = QScrollArea()
        guide_scroll.setWidgetResizable(True)
        guide_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        guide_content = QWidget()
        guide_layout = QVBoxLayout(guide_content)
        guide_layout.setContentsMargins(0, 0, 8, 0)
        guide_layout.setSpacing(20)

        guide_title_lbl = QLabel("📖   Usage & Focus Guide")
        guide_title_lbl.setProperty("class", "subheading")
        guide_layout.addWidget(guide_title_lbl)

        # Introduction card
        intro_card = QFrame()
        intro_card.setProperty("class", "card")
        intro_card_layout = QVBoxLayout(intro_card)
        intro_card_layout.setContentsMargins(20, 20, 20, 20)
        intro_card_layout.setSpacing(10)
        
        intro_header = QLabel("Welcome to Cygnus")
        intro_header.setStyleSheet("font-weight: bold; font-size: 15px; color: #ECFDF5;")
        intro_card_layout.addWidget(intro_header)
        
        intro_text = QLabel(
            "Cygnus is a premium focus dashboard and stopwatch environment tailored to optimize study tracking, visual flow, and syllabus management. Follow the sections below to get the most out of your focus sessions."
        )
        intro_text.setWordWrap(True)
        intro_text.setStyleSheet("color: rgba(203, 170, 205, 0.85); font-size: 13px; line-height: 1.5;")
        intro_card_layout.addWidget(intro_text)
        guide_layout.addWidget(intro_card)

        # Section 1: Focus Timer card
        timer_guide_card = QFrame()
        timer_guide_card.setProperty("class", "card")
        timer_guide_card_layout = QVBoxLayout(timer_guide_card)
        timer_guide_card_layout.setContentsMargins(20, 20, 20, 20)
        timer_guide_card_layout.setSpacing(10)

        tg_header = QLabel("⏱️   Focus Timer & Modes")
        tg_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #ECFDF5;")
        timer_guide_card_layout.addWidget(tg_header)

        tg_text = QLabel(
            "1. <b>Create Subjects First</b>: Go to the 'Subjects' tab in Settings to add all the academic subjects or tasks you want to track.\n\n"
            "2. <b>Select and Start</b>: In the main Timer view, pick your active subject card and press Start to trigger the stopwatch.\n\n"
            "3. <b>Timer Styles</b>:\n"
            "   • <i>Start from Zero (Standard)</i>: stopwatch begins at 00:00:00 every time you launch focus.\n"
            "   • <i>Daily Total Time (Accumulative)</i>: stopwatch preloads your day's total focus time and adds your session duration on top of it automatically."
        )
        tg_text.setWordWrap(True)
        tg_text.setStyleSheet("color: rgba(203, 170, 205, 0.85); font-size: 12px; line-height: 1.5;")
        timer_guide_card_layout.addWidget(tg_text)
        guide_layout.addWidget(timer_guide_card)

        # Section 2: Custom Layouts & Aesthetics card
        aes_guide_card = QFrame()
        aes_guide_card.setProperty("class", "card")
        aes_guide_card_layout = QVBoxLayout(aes_guide_card)
        aes_guide_card_layout.setContentsMargins(20, 20, 20, 20)
        aes_guide_card_layout.setSpacing(10)

        ag_header = QLabel("🎨   Visuals & Glassmorphism")
        ag_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #ECFDF5;")
        aes_guide_card_layout.addWidget(ag_header)

        ag_text = QLabel(
            "1. <b>Custom Backgrounds</b>: Choose high-definition wallpapers from 'Visuals & Theme' to act as your custom glass backing.\n\n"
            "2. <b>Image Customizations</b>: Adjust background Gaussian Blur intensity and overlay brightness in real-time to maximize font contrast and maintain reading flow.\n\n"
            "3. <b>Accent Themes</b>: Shift accent colors instantly (Amber, Emerald, Rosy, etc.) to match your mood and aesthetic preference."
        )
        ag_text.setWordWrap(True)
        ag_text.setStyleSheet("color: rgba(203, 170, 205, 0.85); font-size: 12px; line-height: 1.5;")
        aes_guide_card_layout.addWidget(ag_text)
        guide_layout.addWidget(aes_guide_card)

        # Section 3: Keyboard & Data card
        sys_guide_card = QFrame()
        sys_guide_card.setProperty("class", "card")
        sys_guide_card_layout = QVBoxLayout(sys_guide_card)
        sys_guide_card_layout.setContentsMargins(20, 20, 20, 20)
        sys_guide_card_layout.setSpacing(10)

        sg_header = QLabel("📦   Data Security & Backups")
        sg_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #ECFDF5;")
        sys_guide_card_layout.addWidget(sg_header)

        sg_text = QLabel(
            "1. <b>Automated Storage</b>: Every single study session is logged locally inside an SQLite database to ensure offline stability.\n\n"
            "2. <b>Logs Export</b>: Use the '📥 Export Study Log' button under System settings to extract your study sessions into `.csv` spreadsheets for Excel/Sheets analysis.\n\n"
            "3. <b>Reset All Data</b>: Permanently wipe logs, tasks, profile pictures, and event deadlines when starting a new academic year."
        )
        sg_text.setWordWrap(True)
        sg_text.setStyleSheet("color: rgba(203, 170, 205, 0.85); font-size: 12px; line-height: 1.5;")
        sys_guide_card_layout.addWidget(sg_text)
        guide_layout.addWidget(sys_guide_card)

        guide_scroll.setWidget(guide_content)
        
        guide_layout_outer = QVBoxLayout(self._page_guide)
        guide_layout_outer.setContentsMargins(0, 0, 0, 0)
        guide_layout_outer.addWidget(guide_scroll)

        self._stacked_widget.addWidget(self._page_guide)

        splitter.addWidget(self._stacked_card)
        splitter.setSizes([220, 780])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        content_layout.addWidget(splitter, stretch=1)

        outer_layout.addWidget(content_widget, stretch=1)

        # Default sub-page is Subjects (Page 0)
        self._switch_sub_page(0)

    def _switch_sub_page(self, index: int):
        self._stacked_widget.setCurrentIndex(index)
        self._update_nav_styles(index)

    def _update_nav_styles(self, active_idx: int):
        for idx, btn in enumerate(self._nav_buttons):
            is_active = (idx == active_idx)
            btn.setChecked(is_active)
            
            # Active vs inactive styling
            if is_active:
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding-left: 18px;
                        background: rgba(16, 185, 129, 0.22);
                        color: #FFFFFF;
                        font-weight: bold;
                        border-left: 3px solid #10B981;
                        border-top-left-radius: 0px;
                        border-bottom-left-radius: 0px;
                        border-top-right-radius: 8px;
                        border-bottom-right-radius: 8px;
                        border-top: none; border-right: none; border-bottom: none;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding-left: 18px;
                        background: transparent;
                        color: rgba(203, 170, 205, 0.8);
                        font-weight: 500;
                        border: none;
                        border-radius: 8px;
                    }
                    QPushButton:hover {
                        background: rgba(16, 185, 129, 0.08);
                        color: #10B981;
                    }
                """)



    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("class", "subheading")
        return label

    def _add_separator(self, layout):
        sep = QFrame()
        sep.setProperty("class", "separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

    # ---------- Subject Management ----------

    def _refresh_subjects(self):
        while self._subjects_container.count():
            item = self._subjects_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for subj in subject_manager.list_subjects():
            card = QFrame()
            card.setProperty("class", "card")
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 8, 12, 8)
            row.setSpacing(12)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {subj.color_hex}; font-size: 18px;")
            dot.setFixedWidth(20)
            row.addWidget(dot)

            name = QLabel(subj.name)
            name.setStyleSheet("font-weight: bold;")
            row.addWidget(name, stretch=1)

            color_label = QLabel(subj.color_hex)
            color_label.setProperty("class", "caption")
            row.addWidget(color_label)

            edit_btn = QPushButton("✏️")
            edit_btn.setProperty("class", "icon-btn")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, s=subj: self._edit_subject(s))
            row.addWidget(edit_btn)

            del_btn = QPushButton("✕")
            del_btn.setProperty("class", "icon-btn")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet("color: #FF6B6B;")
            del_btn.clicked.connect(lambda checked, s=subj: self._delete_subject(s))
            row.addWidget(del_btn)

            self._subjects_container.addWidget(card)

    def _add_subject(self):
        from app.ui.widgets.subject_picker import SubjectDialog
        dialog = SubjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, color = dialog.get_values()
            if name:
                subject_manager.create_subject(name, color)
                self._refresh_subjects()

    def _edit_subject(self, subject: Subject):
        from app.ui.widgets.subject_picker import SubjectDialog
        dialog = SubjectDialog(self, subject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, color = dialog.get_values()
            if name:
                subject_manager.update_subject(subject.id, name, color)
                self._refresh_subjects()

    def _delete_subject(self, subject: Subject):
        reply = QMessageBox.question(
            self,
            "Delete Subject",
            f"Delete '{subject.name}'? Sessions using this subject will keep their data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            subject_manager.delete_subject(subject.id)
            self._refresh_subjects()

    # ---------- D-Day Management ----------

    def _refresh_dday(self):
        while self._dday_container.count():
            item = self._dday_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        events = dday_manager.list_events()
        if not events:
            empty = QLabel("No D-Day events yet.")
            empty.setProperty("class", "muted")
            self._dday_container.addWidget(empty)
            return

        for evt in events:
            card = QFrame()
            card.setProperty("class", "card")
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 8, 12, 8)
            row.setSpacing(12)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {evt.color_hex}; font-size: 18px;")
            dot.setFixedWidth(20)
            row.addWidget(dot)

            name = QLabel(evt.title)
            name.setStyleSheet("font-weight: bold;")
            row.addWidget(name, stretch=1)

            days = dday_manager.get_days_remaining(evt)
            if days > 0:
                dday_text = f"D-{days}"
            elif days == 0:
                dday_text = "D-DAY"
            else:
                dday_text = f"D+{abs(days)}"

            dday_label = QLabel(dday_text)
            dday_label.setStyleSheet("font-weight: bold; color: #FDCB6E;")
            row.addWidget(dday_label)

            date_label = QLabel(evt.target_date.strftime("%Y-%m-%d"))
            date_label.setProperty("class", "caption")
            row.addWidget(date_label)

            del_btn = QPushButton("✕")
            del_btn.setProperty("class", "icon-btn")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet("color: #FF6B6B;")
            del_btn.clicked.connect(lambda checked, e=evt: self._delete_dday(e))
            row.addWidget(del_btn)

            self._dday_container.addWidget(card)

    def _add_dday(self):
        dialog = DDayDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, target, color = dialog.get_values()
            if title:
                dday_manager.create_event(title, target, color)
                self._refresh_dday()

    def _delete_dday(self, event: DDayEvent):
        reply = QMessageBox.warning(
            self,
            "Delete Event",
            f"Are you sure you want to delete the event '{event.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            dday_manager.delete_event(event.id)
            self._refresh_dday()

    # ---------- Background Image ----------

    def _build_bg_ui(self):
        """Build the background image controls UI."""
        from app.core import background_manager as bm

        # Preview label
        self._bg_preview = QLabel()
        self._bg_preview.setFixedSize(320, 160)
        self._bg_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bg_preview.setStyleSheet("""
            border: 2px dashed #065F46;
            border-radius: 12px;
            background-color: rgba(42, 44, 49, 0.5);
            color: #6EE7B7;
            font-size: 13px;
        """)
        self._bg_preview.setText("No background image set.\nClick 'Choose Image' to browse.")
        self._bg_container.addWidget(self._bg_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        choose_btn = QPushButton("🖼  Choose Image")
        choose_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        choose_btn.clicked.connect(self._pick_bg_image)
        btn_row.addWidget(choose_btn)

        self._remove_bg_btn = QPushButton("✕  Remove")
        self._remove_bg_btn.setProperty("class", "danger-btn")
        self._remove_bg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._remove_bg_btn.clicked.connect(self._remove_bg_image)
        self._remove_bg_btn.setEnabled(bm.is_bg_enabled())
        btn_row.addWidget(self._remove_bg_btn)
        btn_row.addStretch()
        self._bg_container.addLayout(btn_row)

        # Blur slider
        blur_lbl_row = QHBoxLayout()
        blur_lbl = QLabel("Gaussian Blur Intensity")
        blur_lbl.setStyleSheet("color: #6EE7B7; font-size: 13px;")
        self._blur_val_lbl = QLabel(f"{bm.get_blur_radius()}")
        self._blur_val_lbl.setStyleSheet("color: #ECFDF5; font-size: 13px; font-weight: 600; min-width: 28px;")
        blur_lbl_row.addWidget(blur_lbl)
        blur_lbl_row.addStretch()
        blur_lbl_row.addWidget(self._blur_val_lbl)
        self._bg_container.addLayout(blur_lbl_row)

        self._blur_slider = QSlider(Qt.Orientation.Horizontal)
        self._blur_slider.setMinimum(0)
        self._blur_slider.setMaximum(40)
        self._blur_slider.setValue(bm.get_blur_radius())
        self._blur_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #065F46;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #10B981;
                border: none;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #10B981;
                border-radius: 3px;
            }
        """)
        self._blur_slider.valueChanged.connect(self._on_blur_changed)
        self._bg_container.addWidget(self._blur_slider)

        # Brightness / overlay opacity slider
        op_lbl_row = QHBoxLayout()
        op_lbl = QLabel("Image Brightness")
        op_lbl.setStyleSheet("color: #6EE7B7; font-size: 13px;")
        opacity_pct = int(bm.get_opacity() * 100)
        self._op_val_lbl = QLabel(f"{opacity_pct}%")
        self._op_val_lbl.setStyleSheet("color: #ECFDF5; font-size: 13px; font-weight: 600; min-width: 36px;")
        op_lbl_row.addWidget(op_lbl)
        op_lbl_row.addStretch()
        op_lbl_row.addWidget(self._op_val_lbl)
        self._bg_container.addLayout(op_lbl_row)

        self._op_slider = QSlider(Qt.Orientation.Horizontal)
        self._op_slider.setMinimum(0)
        self._op_slider.setMaximum(90)    # 0% = full brightness, 90% = near-black
        self._op_slider.setValue(opacity_pct)
        self._op_slider.setStyleSheet(self._blur_slider.styleSheet())
        self._op_slider.valueChanged.connect(self._on_opacity_changed)
        self._bg_container.addWidget(self._op_slider)

        # Load preview if image exists
        self._refresh_bg_preview()

    def _refresh_bg_preview(self):
        """Show a thumbnail preview of the current background image."""
        from app.core import background_manager as bm
        if bm.is_bg_enabled():
            from PySide6.QtGui import QPixmap
            px = QPixmap(str(bm.get_bg_image_path()))
            if not px.isNull():
                px = px.scaled(
                    320, 160,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                # Center-crop
                x = (px.width() - 320) // 2
                y = (px.height() - 160) // 2
                px = px.copy(x, y, 320, 160)
                self._bg_preview.setPixmap(px)
                self._bg_preview.setText("")
                self._remove_bg_btn.setEnabled(True)
                return
        self._bg_preview.clear()
        self._bg_preview.setText("No background image set.\nClick 'Choose Image' to browse.")
        self._remove_bg_btn.setEnabled(False)

    def _pick_bg_image(self):
        from app.core import background_manager as bm
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not path:
            return
        ok = bm.save_bg_image(path)
        if ok:
            self._refresh_bg_preview()
            self._apply_bg_to_window()
        else:
            QMessageBox.warning(self, "Error", "Could not load the selected image.")

    def _remove_bg_image(self):
        from app.core import background_manager as bm
        bm.remove_bg_image()
        self._refresh_bg_preview()
        self._apply_bg_to_window()

    def _on_blur_changed(self, value: int):
        from app.core import background_manager as bm
        self._blur_val_lbl.setText(str(value))
        bm.save_blur(value)
        self._apply_bg_to_window()

    def _on_opacity_changed(self, value: int):
        from app.core import background_manager as bm
        self._op_val_lbl.setText(f"{value}%")
        bm.save_opacity(value / 100.0)
        self._apply_bg_to_window()

    def _apply_bg_to_window(self):
        """Trigger the main window to reload and repaint the background."""
        window = self.window()
        if hasattr(window, "reload_background"):
            window.reload_background()

    def _on_timer_style_changed(self, index):
        mode = self._timer_mode_combo.itemData(index)
        save_setting("timer_style", mode)

    def _on_show_trackers_changed(self, state):
        """Save preference and trigger sidebar reload."""
        is_checked = (state == 2)  # Qt.CheckState.Checked is 2
        save_setting("show_optional_trackers", is_checked)
        
        # Trigger dynamic sidebar reloading if sidebar is accessible via MainWindow parent
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "sidebar") and hasattr(parent.sidebar, "reload_sidebar"):
                parent.sidebar.reload_sidebar()
                break
            parent = parent.parent()

    # ---------- Appearance / Theme ----------
    def _change_theme(self, theme_name: str):
        from app.core.theme_manager import apply_theme, THEMES
        from pathlib import Path
        
        # Apply the theme which updates files and reloads QSS
        app_dir = Path(__file__).parent.parent
        apply_theme(theme_name, app_dir)
        
        # Update styling of all buttons dynamically so the selection updates visually in real-time
        for name, btn in getattr(self, "_theme_buttons", {}).items():
            t_colors = THEMES[name]
            accent = t_colors["accent"]
            is_active = (name == theme_name)
            border_color = accent if is_active else "#065F46"
            border_width = "2px" if is_active else "1px"
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(30, 10, 35, 0.45);
                    border: {border_width} solid {border_color};
                    border-radius: 10px;
                    color: {accent};
                    font-weight: 600;
                    text-align: left;
                    padding-left: 14px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    border-color: {accent};
                    background-color: rgba(16, 185, 129, 0.08);
                }}
            """)
            
        QMessageBox.information(
            self, 
            "Theme Updated", 
            f"The '{theme_name}' theme has been applied globally.\n\nRestart the application to see the changes take full effect across all elements."
        )

    # ---------- Data Management ----------

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Sessions", "pytp_sessions.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        sessions = session_manager.get_sessions_for_range(
            date(2000, 1, 1), date(2100, 1, 1)
        )

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Subject", "Start", "End", "Duration (s)", "Notes"])
            for s in sessions:
                subj = subject_manager.get_subject(s.subject_id)
                writer.writerow([
                    s.id,
                    subj.name if subj else "Unknown",
                    s.start_time.isoformat(),
                    s.end_time.isoformat(),
                    s.duration_seconds,
                    s.notes,
                ])

        QMessageBox.information(self, "Export Complete", f"Exported {len(sessions)} sessions to:\n{path}")

    def _reset_data(self):
        reply = QMessageBox.warning(
            self,
            "Reset All Data",
            "⚠ This will permanently delete ALL sessions, tasks, events, profile data, and settings.\n\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Double confirm
            reply2 = QMessageBox.critical(
                self,
                "Final Confirmation",
                "This action CANNOT be undone.\nProfile picture and all data will be lost.\n\nProceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply2 == QMessageBox.StandardButton.Yes:
                # Reset all data and notify other pages
                from app.core.data_reset import reset_all_data
                from app.core.events import app_events

                reset_all_data()
                self._refresh_subjects()
                self._refresh_dday()

                # Notify all other pages to refresh
                app_events.data_reset.emit()

                QMessageBox.information(self, "Reset Complete", "All data has been reset. The app is now fresh.")

    # Update checking methods completely removed

    def _open_contact(self):
        """Open the contact us dialog."""
        dialog = ContactDialog(self)
        dialog.exec()

    def _open_report(self):
        """Open the report issue dialog."""
        dialog = ReportDialog(self)
        dialog.exec()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_subjects()
        self._refresh_dday()


class DDayDialog(QDialog):
    """Dialog for creating a D-Day event."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New D-Day Event")
        self.setFixedSize(360, 260)
        self._color = "#FDCB6E"

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Title
        layout.addWidget(QLabel("Event Name"))
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("e.g., Final Exam")
        layout.addWidget(self._title_input)

        # Date
        layout.addWidget(QLabel("Target Date"))
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(date.today())
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self._date_edit)

        # Color
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color"))
        self._color_preview = QPushButton()
        self._color_preview.setFixedSize(28, 28)
        self._color_preview.setStyleSheet(
            f"background-color: {self._color}; border: none; border-radius: 14px;"
        )
        self._color_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color_preview.clicked.connect(self._pick_color)
        color_row.addWidget(self._color_preview)
        color_row.addStretch()
        layout.addLayout(color_row)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "ghost")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self)
        if color.isValid():
            self._color = color.name()
            self._color_preview.setStyleSheet(
                f"background-color: {self._color}; border: none; border-radius: 14px;"
            )

    def get_values(self) -> tuple[str, date, str]:
        return (
            self._title_input.text().strip(),
            self._date_edit.date().toPyDate(),
            self._color,
        )
