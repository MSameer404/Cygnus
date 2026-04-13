# src/app/ui/profile_dialog.py
"""User profile dialog with view and edit modes, and profile picture upload."""

from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from app.core import profile_manager


class ProfileDialog(QDialog):
    """Profile dialog with view/edit toggle via pencil icon."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("My Profile")
        self.setFixedSize(460, 580)
        self.setObjectName("profileDialog")
        self._editing = False
        self._profile_data = profile_manager.get_profile()
        self._pending_picture_path: str | None = None  # temp path before save
        self._setup_ui()
        self._populate_view()

    # ------------------------------------------------------------------ UI
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Top hero section (avatar + name) ----
        hero = QWidget()
        hero.setObjectName("profileHero")
        hero.setFixedHeight(180)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.setSpacing(10)

        # Avatar container (square, with optional upload overlay)
        avatar_container = QWidget()
        avatar_container.setFixedSize(88, 88)
        avatar_stack = QVBoxLayout(avatar_container)
        avatar_stack.setContentsMargins(0, 0, 0, 0)
        avatar_stack.setSpacing(0)

        # The avatar label shows either the uploaded image or initials
        self._avatar = QLabel()
        self._avatar.setObjectName("profileAvatar")
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFixedSize(88, 88)
        avatar_stack.addWidget(self._avatar)

        hero_layout.addWidget(avatar_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Upload button (visible in edit mode only, overlaid near avatar)
        self._upload_btn = QPushButton("📷 Change Photo")
        self._upload_btn.setProperty("class", "ghost")
        self._upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._upload_btn.setFixedHeight(28)
        self._upload_btn.setStyleSheet(
            "font-size: 11px; padding: 4px 12px; border-radius: 6px;"
        )
        self._upload_btn.clicked.connect(self._pick_profile_picture)
        self._upload_btn.hide()
        hero_layout.addWidget(self._upload_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Remove photo button (visible in edit mode if picture exists)
        self._remove_pic_btn = QPushButton("✕ Remove Photo")
        self._remove_pic_btn.setProperty("class", "ghost")
        self._remove_pic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._remove_pic_btn.setFixedHeight(24)
        self._remove_pic_btn.setStyleSheet(
            "font-size: 10px; padding: 2px 8px; color: #FF6B6B; border-color: #FF6B6B;"
        )
        self._remove_pic_btn.clicked.connect(self._remove_profile_picture)
        self._remove_pic_btn.hide()
        hero_layout.addWidget(
            self._remove_pic_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Name label (view mode)
        self._name_label = QLabel()
        self._name_label.setObjectName("profileNameLabel")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 18)
        font.setBold(True)
        self._name_label.setFont(font)
        hero_layout.addWidget(self._name_label, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addWidget(hero)

        # ---- Edit toggle button (pencil) ----
        edit_bar = QHBoxLayout()
        edit_bar.setContentsMargins(24, 8, 24, 0)
        edit_bar.addStretch()

        self._edit_btn = QPushButton("✏️  Edit Profile")
        self._edit_btn.setProperty("class", "ghost")
        self._edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_btn.setFixedHeight(34)
        self._edit_btn.clicked.connect(self._toggle_edit)
        edit_bar.addWidget(self._edit_btn)

        root.addLayout(edit_bar)

        # ---- Scrollable content area ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self._form_layout = QVBoxLayout(content)
        self._form_layout.setContentsMargins(28, 16, 28, 20)
        self._form_layout.setSpacing(18)

        # ----- Name -----
        self._name_view, self._name_edit_container, self._name_input = (
            self._make_field("Name", "Your name")
        )

        # ----- Class / Grade -----
        self._class_view, self._class_edit_container, self._class_input = (
            self._make_field("Class / Grade", "e.g., 12th, 2nd Year")
        )

        # ----- Target Exam -----
        self._exam_view, self._exam_edit_container, self._exam_input = (
            self._make_field("Target Exam", "e.g., JEE Advanced 2027")
        )

        # ----- Daily Study Goal -----
        goal_group = QVBoxLayout()
        goal_group.setSpacing(4)

        goal_label = QLabel("Daily Study Goal")
        goal_label.setProperty("class", "profile-field-label")
        goal_group.addWidget(goal_label)

        # View
        self._goal_view = QLabel()
        self._goal_view.setProperty("class", "profile-field-value")
        goal_group.addWidget(self._goal_view)

        # Edit
        self._goal_edit_container = QWidget()
        goal_edit_layout = QHBoxLayout(self._goal_edit_container)
        goal_edit_layout.setContentsMargins(0, 0, 0, 0)
        goal_edit_layout.setSpacing(8)

        self._goal_spin = QDoubleSpinBox()
        self._goal_spin.setRange(0.5, 24.0)
        self._goal_spin.setSingleStep(0.5)
        self._goal_spin.setSuffix(" hours")
        self._goal_spin.setDecimals(1)
        goal_edit_layout.addWidget(self._goal_spin)
        goal_edit_layout.addStretch()

        self._goal_edit_container.hide()
        goal_group.addWidget(self._goal_edit_container)

        self._form_layout.addLayout(goal_group)

        # Separator
        self._add_separator()

        # ----- Start Date -----
        date_group = QVBoxLayout()
        date_group.setSpacing(4)

        date_label = QLabel("Journey Start Date")
        date_label.setProperty("class", "profile-field-label")
        date_group.addWidget(date_label)

        # View
        self._date_view = QLabel()
        self._date_view.setProperty("class", "profile-field-value")
        date_group.addWidget(self._date_view)

        # Edit
        self._date_edit_container = QWidget()
        date_edit_layout = QHBoxLayout(self._date_edit_container)
        date_edit_layout.setContentsMargins(0, 0, 0, 0)
        date_edit_layout.setSpacing(8)

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setDate(date.today())
        date_edit_layout.addWidget(self._date_edit)
        date_edit_layout.addStretch()

        self._date_edit_container.hide()
        date_group.addWidget(self._date_edit_container)

        self._form_layout.addLayout(date_group)

        # ---- Completeness indicator ----
        self._add_separator()
        self._completeness_label = QLabel()
        self._completeness_label.setObjectName("profileCompleteness")
        self._completeness_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._form_layout.addWidget(self._completeness_label)

        # ---- Save / Cancel buttons (edit mode only) ----
        self._btn_container = QWidget()
        btn_layout = QHBoxLayout(self._btn_container)
        btn_layout.setContentsMargins(0, 8, 0, 0)
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "ghost")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self._cancel_edit)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾  Save")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_profile)
        btn_layout.addWidget(save_btn)

        self._btn_container.hide()
        self._form_layout.addWidget(self._btn_container)

        self._form_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    # ------------------------------------------------------------------ helpers
    def _make_field(self, label_text: str, placeholder: str):
        """Create a view label + hidden edit input for a text field."""
        group = QVBoxLayout()
        group.setSpacing(4)

        label = QLabel(label_text)
        label.setProperty("class", "profile-field-label")
        group.addWidget(label)

        # View mode value
        view_label = QLabel()
        view_label.setProperty("class", "profile-field-value")
        group.addWidget(view_label)

        # Edit mode input (hidden by default)
        edit_container = QWidget()
        edit_layout = QHBoxLayout(edit_container)
        edit_layout.setContentsMargins(0, 0, 0, 0)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        edit_layout.addWidget(line_edit)

        edit_container.hide()
        group.addWidget(edit_container)

        self._form_layout.addLayout(group)
        self._add_separator()

        return view_label, edit_container, line_edit

    def _add_separator(self):
        sep = QFrame()
        sep.setProperty("class", "separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        self._form_layout.addWidget(sep)

    def _load_avatar_pixmap(self, path: str | Path | None = None):
        """Load and display a square profile picture in the avatar label."""
        pic_path = path or profile_manager.get_profile_picture_path()
        if pic_path and Path(str(pic_path)).exists():
            pixmap = QPixmap(str(pic_path))
            # Crop to square from center
            w, h = pixmap.width(), pixmap.height()
            if w != h:
                side = min(w, h)
                x = (w - side) // 2
                y = (h - side) // 2
                pixmap = pixmap.copy(x, y, side, side)
            # Scale to avatar size
            pixmap = pixmap.scaled(
                88, 88,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._avatar.setPixmap(pixmap)
            self._avatar.setText("")  # clear any text
            return True
        return False

    # ------------------------------------------------------------------ data
    def _populate_view(self):
        """Fill view-mode labels from profile data."""
        data = self._profile_data

        name = data.get("name", "") or "Cygnus"
        self._name_label.setText(name)

        # Avatar — show profile picture if available, else show initial
        if not self._load_avatar_pixmap():
            initial = name[0].upper() if name else "C"
            self._avatar.setPixmap(QPixmap())  # clear pixmap
            self._avatar.setText(initial)

        # Show/hide remove button
        has_pic = profile_manager.get_profile_picture_path() is not None
        self._remove_pic_btn.setVisible(self._editing and has_pic)

        # Field values
        self._name_view.setText(name if name != "Cygnus" else "Cygnus (default)")
        self._class_view.setText(data.get("class", "") or "Not set")
        self._exam_view.setText(data.get("target_exam", "") or "Not set")

        goal = data.get("daily_goal_hours", "6")
        try:
            goal_f = float(goal)
        except ValueError:
            goal_f = 6.0
        self._goal_view.setText(f"{goal_f:g} hours / day")

        start = data.get("start_date", "")
        if start:
            try:
                sd = date.fromisoformat(start)
                days = (date.today() - sd).days
                self._date_view.setText(f"{start}  ({days} days ago)")
            except ValueError:
                self._date_view.setText(start)
        else:
            self._date_view.setText("Not set")

        # Grey out "Not set" values
        for lbl in (self._class_view, self._exam_view, self._date_view):
            if lbl.text().startswith("Not set"):
                lbl.setStyleSheet("color: #8B8BA0; font-style: italic;")
            else:
                lbl.setStyleSheet("")
        if self._name_view.text().endswith("(default)"):
            self._name_view.setStyleSheet("color: #8B8BA0; font-style: italic;")
        else:
            self._name_view.setStyleSheet("")

        # Completeness
        filled = 0
        total = 5
        if data.get("name", "") and data.get("name", "") != "Cygnus":
            filled += 1
        if data.get("class", ""):
            filled += 1
        if data.get("target_exam", ""):
            filled += 1
        if data.get("daily_goal_hours", ""):
            filled += 1
        if data.get("start_date", ""):
            filled += 1
        pct = int(filled / total * 100)
        self._completeness_label.setText(
            f"Profile {pct}% complete  ({'⬤' * filled}{'◯' * (total - filled)})"
        )

    def _populate_edit(self):
        """Fill edit inputs from profile data."""
        data = self._profile_data

        name = data.get("name", "")
        self._name_input.setText(name if name != "Cygnus" else "")
        self._class_input.setText(data.get("class", ""))
        self._exam_input.setText(data.get("target_exam", ""))

        try:
            goal = float(data.get("daily_goal_hours", "6"))
        except ValueError:
            goal = 6.0
        self._goal_spin.setValue(goal)

        start = data.get("start_date", "")
        if start:
            try:
                self._date_edit.setDate(date.fromisoformat(start))
            except ValueError:
                self._date_edit.setDate(date.today())
        else:
            self._date_edit.setDate(date.today())

    # ------------------------------------------------------------------ picture
    def _pick_profile_picture(self):
        """Open a file dialog to select a profile picture."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Picture",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)",
        )
        if path:
            self._pending_picture_path = path
            # Preview immediately in the avatar
            self._load_avatar_pixmap(path)
            # Show remove button
            self._remove_pic_btn.show()

    def _remove_profile_picture(self):
        """Remove the profile picture (takes effect on save)."""
        self._pending_picture_path = "__REMOVE__"
        self._avatar.setPixmap(QPixmap())  # clear pixmap
        name = self._name_input.text().strip() or self._profile_data.get("name", "") or "Cygnus"
        self._avatar.setText(name[0].upper() if name else "C")
        self._remove_pic_btn.hide()

    # ------------------------------------------------------------------ modes
    def _toggle_edit(self):
        if self._editing:
            self._cancel_edit()
        else:
            self._enter_edit()

    def _enter_edit(self):
        self._editing = True
        self._pending_picture_path = None
        self._edit_btn.setText("✕  Cancel Edit")
        self._populate_edit()
        # Show edit widgets, hide view widgets
        for view, edit in self._view_edit_pairs():
            view.hide()
            edit.show()
        self._btn_container.show()
        self._upload_btn.show()
        # Show remove button if picture already exists
        has_pic = profile_manager.get_profile_picture_path() is not None
        self._remove_pic_btn.setVisible(has_pic)

    def _cancel_edit(self):
        self._editing = False
        self._pending_picture_path = None
        self._edit_btn.setText("✏️  Edit Profile")
        # Hide edit widgets, show view widgets
        for view, edit in self._view_edit_pairs():
            edit.hide()
            view.show()
        self._btn_container.hide()
        self._upload_btn.hide()
        self._remove_pic_btn.hide()
        # Restore avatar to saved state
        self._populate_view()

    def _save_profile(self):
        name = self._name_input.text().strip() or "Cygnus"
        data = {
            "name": name,
            "class": self._class_input.text().strip(),
            "target_exam": self._exam_input.text().strip(),
            "daily_goal_hours": str(self._goal_spin.value()),
            "start_date": self._date_edit.date().toPyDate().isoformat(),
        }
        profile_manager.save_profile(data)

        # Handle profile picture
        if self._pending_picture_path == "__REMOVE__":
            profile_manager.remove_profile_picture()
        elif self._pending_picture_path:
            profile_manager.save_profile_picture(self._pending_picture_path)

        self._profile_data = profile_manager.get_profile()
        self._pending_picture_path = None
        self._cancel_edit()  # switch back to view mode
        self._populate_view()

    def _view_edit_pairs(self):
        """Return (view_widget, edit_widget) pairs for toggling."""
        return [
            (self._name_view, self._name_edit_container),
            (self._class_view, self._class_edit_container),
            (self._exam_view, self._exam_edit_container),
            (self._goal_view, self._goal_edit_container),
            (self._date_view, self._date_edit_container),
        ]
