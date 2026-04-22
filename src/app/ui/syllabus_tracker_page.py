# src/app/ui/syllabus_tracker_page.py
"""Syllabus Tracker page with per-subject chapter/material tables."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core import subject_manager as sm
from app.core import syllabus_manager as slm


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

PRIORITIES = ["High", "Medium", "Low"]

PRIORITY_COLORS = {
    "High": "#F43F5E",
    "Medium": "#F59E0B",
    "Low": "#8B8BA0",
}


def _colored_dot(color_hex: str, size: int = 10) -> QLabel:
    lbl = QLabel("●")
    lbl.setStyleSheet(f"color: {color_hex}; font-size: {size}px; background: transparent;")
    return lbl


class PriorityButton(QPushButton):
    """A priority drop-down picker built on QPushButton.

    Uses a QMenu for selection to avoid the QComboBox ::drop-down
    sub-control styling issues on Windows.
    """

    priority_changed = pyqtSignal(str)  # emits new priority string

    _CYCLE = ["High", "Medium", "Low"]

    _BG = {
        "High":   "rgba(244, 63,  94,  0.18)",
        "Medium": "rgba(245, 158, 11,  0.18)",
        "Low":    "rgba(139, 139, 160, 0.18)",
    }
    _FG = {
        "High":   "#FB7185",
        "Medium": "#FCD34D",
        "Low":    "#A0A0B8",
    }
    _BORDER = {
        "High":   "rgba(244, 63,  94,  0.55)",
        "Medium": "rgba(245, 158, 11,  0.55)",
        "Low":    "rgba(139, 139, 160, 0.40)",
    }

    def __init__(self, priority: str = "Medium", parent=None):
        super().__init__(parent)
        self._priority = priority
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_menu()
        self._apply_style()

    def _setup_menu(self):
        menu = QMenu(self)
        for p in self._CYCLE:
            act = menu.addAction(p)
            act.triggered.connect(lambda _, prio=p: self._set_and_emit(prio))
        self.setMenu(menu)

    def _apply_style(self):
        p = self._priority
        self.setText(f"{p}  ▾")
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self._BG[p]};
                color: {self._FG[p]};
                border: 1px solid {self._BORDER[p]};
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {self._BORDER[p]};
                color: #FFFFFF;
            }}
            QPushButton::menu-indicator {{
                image: none;
            }}
            """
        )

    def _set_and_emit(self, prio: str):
        if self._priority != prio:
            self._priority = prio
            self._apply_style()
            self.priority_changed.emit(self._priority)

    def set_priority(self, priority: str):
        """Set priority without emitting signal."""
        self._priority = priority
        self._apply_style()

    @property
    def priority(self) -> str:
        return self._priority


# ─────────────────────────────────────────────────────────────
# Dialogs
# ─────────────────────────────────────────────────────────────

class _AddChapterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Chapter")
        self.setMinimumWidth(340)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 20, 20, 20)

        lay.addWidget(QLabel("Chapter name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Kinematics")
        lay.addWidget(self.name_edit)

        lay.addWidget(QLabel("Priority:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(PRIORITIES)
        self.priority_combo.setCurrentIndex(1)
        lay.addWidget(self.priority_combo)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def values(self):
        return self.name_edit.text().strip(), self.priority_combo.currentText()


class _AddMaterialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Material")
        self.setMinimumWidth(300)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 20, 20, 20)

        lay.addWidget(QLabel("Material name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. DPP, NCERT, PYQ")
        lay.addWidget(self.name_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def value(self):
        return self.name_edit.text().strip()


class _SettingsDialog(QDialog):
    """Gear-button dialog to manage subjects (add / delete)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Subjects")
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)
        self._pending_color = "#6C5CE7"

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)

        # ── title bar ──
        title_bar = QWidget()
        title_bar.setObjectName("syllabusSettingsHeader")
        tb_lay = QHBoxLayout(title_bar)
        tb_lay.setContentsMargins(20, 16, 20, 16)
        title_lbl = QLabel("Manage Subjects")
        title_lbl.setProperty("class", "subheading")
        tb_lay.addWidget(title_lbl)
        lay.addWidget(title_bar)

        sep = QFrame()
        sep.setObjectName("headerSeparator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        # ── subject list ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(16, 12, 16, 12)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_widget)
        lay.addWidget(scroll, stretch=1)

        # ── add area ──
        add_frame = QFrame()
        add_frame.setObjectName("syllabusAddArea")
        add_lay = QVBoxLayout(add_frame)
        add_lay.setContentsMargins(16, 12, 16, 12)
        add_lay.setSpacing(8)

        add_lay.addWidget(QLabel("New subject name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Biology")
        add_lay.addWidget(self._name_edit)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color:"))
        self._color_preview = QPushButton()
        self._color_preview.setFixedSize(28, 28)
        self._color_preview.setProperty("class", "syllabus-color-swatch")
        self._color_preview.clicked.connect(self._pick_color)
        self._apply_swatch(self._pending_color)
        color_row.addWidget(self._color_preview)
        color_row.addStretch()
        add_lay.addLayout(color_row)

        add_btn = QPushButton("＋  Add Subject")
        add_btn.clicked.connect(self._add_subject)
        add_lay.addWidget(add_btn)
        lay.addWidget(add_frame)

        self._refresh_list()

    def _apply_swatch(self, color: str):
        self._color_preview.setStyleSheet(
            f"background-color: {color}; border-radius: 6px; border: 2px solid #3D3D60;"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._pending_color), self, "Choose Color")
        if color.isValid():
            self._pending_color = color.name()
            self._apply_swatch(self._pending_color)

    def _refresh_list(self):
        # Clear all except the trailing stretch
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        subjects = sm.list_subjects()
        for subj in subjects:
            row = QFrame()
            row.setObjectName("syllabusSubjectRow")
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(8, 6, 8, 6)
            row_lay.setSpacing(10)
            row_lay.addWidget(_colored_dot(subj.color_hex, 12))
            lbl = QLabel(subj.name)
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row_lay.addWidget(lbl)
            del_btn = QPushButton("✕")
            del_btn.setProperty("class", "syllabus-del-btn")
            del_btn.setFixedSize(28, 28)
            del_btn.clicked.connect(lambda _, sid=subj.id: self._delete_subject(sid))
            row_lay.addWidget(del_btn)
            # Insert before the trailing stretch
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

    def _add_subject(self):
        name = self._name_edit.text().strip()
        if not name:
            return
        sm.create_subject(name, self._pending_color)
        self._name_edit.clear()
        self._refresh_list()

    def _delete_subject(self, subject_id: int):
        reply = QMessageBox.question(
            self, "Delete Subject",
            "Delete this subject and all its syllabus data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            sm.delete_subject(subject_id)
            self._refresh_list()


# ─────────────────────────────────────────────────────────────
# Per-subject syllabus table page
# ─────────────────────────────────────────────────────────────

class SubjectSyllabusPage(QWidget):
    """Full syllabus table for one subject."""

    COL_DEL = 0       # edit-mode delete-row button (hidden normally)
    COL_SNO = 1       # serial number (read-only)
    COL_CHAPTER = 2
    MAT_START = 3     # material columns start here
    # COL_PRIORITY is dynamic: MAT_START + mat_count  (always last)

    def __init__(self, subject, parent=None):
        super().__init__(parent)
        self.subject = subject
        self._edit_mode = False
        self._mat_ids: list[int] = []   # material ids in column order
        self._chapter_ids: list[int] = []
        self._chapter_edits: list = []  # QLineEdit refs for toggling readOnly
        self._building = False
        self._setup_ui()

    # ── setup ──────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 18, 24, 18)
        outer.setSpacing(14)

        # Sub-header row
        hdr = QHBoxLayout()
        hdr.setSpacing(10)

        subj_lbl = QLabel(self.subject.name)
        subj_lbl.setObjectName("syllabusSubjectTitle")
        subj_lbl.setStyleSheet(
            f"color: {self.subject.color_hex}; font-size: 18px; font-weight: bold;"
        )
        hdr.addWidget(subj_lbl)
        hdr.addStretch()

        self._add_ch_btn = QPushButton("＋ Chapter")
        self._add_ch_btn.setProperty("class", "syllabus-action-btn")
        self._add_ch_btn.clicked.connect(self._on_add_chapter)
        hdr.addWidget(self._add_ch_btn)

        self._add_mat_btn = QPushButton("＋ Material")
        self._add_mat_btn.setProperty("class", "syllabus-action-btn")
        self._add_mat_btn.clicked.connect(self._on_add_material)
        hdr.addWidget(self._add_mat_btn)

        self._edit_btn = QPushButton("✎  Edit")
        self._edit_btn.setProperty("class", "secondary")
        self._edit_btn.setCheckable(True)
        self._edit_btn.toggled.connect(self._toggle_edit)
        hdr.addWidget(self._edit_btn)

        outer.addLayout(hdr)

        # Table
        self._table = QTableWidget()
        self._table.setObjectName("syllabusTable")
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.horizontalHeader().setHighlightSections(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        outer.addWidget(self._table, stretch=1)

    # ── refresh ────────────────────────────────────────────

    def refresh(self):
        self._building = True
        chapters = slm.list_chapters(self.subject.id)
        materials = slm.list_materials(self.subject.id)
        self._mat_ids = [m.id for m in materials]
        self._chapter_ids = [c.id for c in chapters]

        mat_count = len(materials)
        col_priority = self.MAT_START + mat_count   # dynamic last column
        total_cols = col_priority + 1
        self._table.setColumnCount(total_cols)
        self._table.setRowCount(len(chapters))

        # Headers: Delete | S.No | Chapter | Mat1..MatN | Priority
        headers = ["", "S.No", "Chapter"] + [m.name for m in materials] + ["Priority"]
        self._table.setHorizontalHeaderLabels(headers)

        # Set column widths
        self._table.setColumnWidth(self.COL_DEL, 36)
        self._table.horizontalHeader().setSectionResizeMode(
            self.COL_SNO, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(self.COL_SNO, 52)
        self._table.horizontalHeader().setSectionResizeMode(
            self.COL_CHAPTER, QHeaderView.ResizeMode.Stretch
        )
        for c in range(self.MAT_START, col_priority):
            self._table.setColumnWidth(c, 110)
        # Priority col: fixed so it never gets clipped at table edge
        self._table.horizontalHeader().setSectionResizeMode(
            col_priority, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(col_priority, 128)

        self._chapter_edits = []
        # Bulk-fetch progress
        ch_ids = [c.id for c in chapters]
        mat_ids_list = [m.id for m in materials]
        progress_map = slm.bulk_get_progress(ch_ids, mat_ids_list)

        for row, chapter in enumerate(chapters):
            self._table.setRowHeight(row, 46)

            # Col 0: delete button (edit mode)
            del_btn = QPushButton("✕")
            del_btn.setProperty("class", "syllabus-del-row-btn")
            del_btn.setFixedSize(28, 28)
            del_btn.clicked.connect(lambda _, cid=chapter.id: self._delete_chapter(cid))
            cell0 = QWidget()
            lay0 = QHBoxLayout(cell0)
            lay0.setContentsMargins(4, 0, 0, 0)
            lay0.addWidget(del_btn)
            self._table.setCellWidget(row, self.COL_DEL, cell0)

            # Col 1: S.No (read-only centered label)
            sno_lbl = QLabel(str(row + 1))
            sno_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sno_lbl.setStyleSheet("color: #8B8BA0; font-size: 12px; background: transparent;")
            self._table.setCellWidget(row, self.COL_SNO, sno_lbl)

            # Col 2: chapter name — read-only normally, editable in edit mode
            ch_edit = QLineEdit(chapter.name)
            ch_edit.setObjectName("syllabusChapterEdit")
            ch_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ch_edit.setReadOnly(not self._edit_mode)
            ch_edit.setCursor(
                Qt.CursorShape.IBeamCursor if self._edit_mode
                else Qt.CursorShape.ArrowCursor
            )
            ch_edit.editingFinished.connect(
                lambda cid=chapter.id, w=ch_edit: slm.update_chapter(cid, name=w.text())
            )
            self._table.setCellWidget(row, self.COL_CHAPTER, ch_edit)
            self._chapter_edits.append(ch_edit)

            # Material columns (cols 2 .. col_priority-1)
            for c_idx, material in enumerate(materials):
                col = self.MAT_START + c_idx
                is_done = progress_map.get((chapter.id, material.id), False)
                cb = QCheckBox()
                cb.setChecked(is_done)
                cb.stateChanged.connect(
                    lambda state, cid=chapter.id, mid=material.id: slm.set_progress(
                        cid, mid, bool(state)
                    )
                )
                cell = QWidget()
                lay = QHBoxLayout(cell)
                lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.addWidget(cb)
                self._table.setCellWidget(row, col, cell)

            # Last col: priority — PriorityButton cycles on click, no sub-control clipping
            prio_btn = PriorityButton(chapter.priority)
            prio_btn.priority_changed.connect(
                lambda prio, cid=chapter.id: self._on_priority_changed(cid, prio)
            )
            prio_cell = QWidget()
            prio_lay = QHBoxLayout(prio_cell)
            prio_lay.setContentsMargins(8, 4, 8, 4)
            prio_lay.addWidget(prio_btn)
            self._table.setCellWidget(row, col_priority, prio_cell)

        # Apply edit-mode visibility
        self._apply_edit_visibility()
        self._update_mat_btn()
        self._rebuild_mat_delete_row()

        self._building = False

    def _rebuild_mat_delete_row(self):
        """Insert/remove a special top row with delete buttons for material columns."""
        mat_count = len(self._mat_ids)
        col_priority = self.MAT_START + mat_count
        if self._edit_mode and self._mat_ids:
            # Check if row 0 is already the delete row
            if self._table.rowCount() == 0 or not self._is_mat_del_row(0):
                self._table.insertRow(0)
                self._table.setRowHeight(0, 32)
                # Fill non-material cols with empty items
                for c in range(self.MAT_START):
                    self._table.setItem(0, c, QTableWidgetItem(""))
                # Fill priority col with empty item too
                self._table.setItem(0, col_priority, QTableWidgetItem(""))
                for c_idx, mid in enumerate(self._mat_ids):
                    col = self.MAT_START + c_idx
                    
                    cell = QWidget()
                    lay = QHBoxLayout(cell)
                    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lay.setContentsMargins(4, 0, 4, 0)
                    lay.setSpacing(4)
                    
                    if c_idx > 0:
                        left_btn = QPushButton("←")
                        left_btn.setProperty("class", "syllabus-move-btn")
                        left_btn.setFixedSize(22, 22)
                        left_btn.clicked.connect(lambda _, m=mid: self._move_material(m, -1))
                        lay.addWidget(left_btn)
                    
                    del_btn = QPushButton("✕ col")
                    del_btn.setProperty("class", "syllabus-del-mat-btn")
                    del_btn.clicked.connect(lambda _, m=mid: self._delete_material(m))
                    lay.addWidget(del_btn)
                    
                    if c_idx < len(self._mat_ids) - 1:
                        right_btn = QPushButton("→")
                        right_btn.setProperty("class", "syllabus-move-btn")
                        right_btn.setFixedSize(22, 22)
                        right_btn.clicked.connect(lambda _, m=mid: self._move_material(m, 1))
                        lay.addWidget(right_btn)
                        
                    self._table.setCellWidget(0, col, cell)
        else:
            # Remove delete row if present
            if self._table.rowCount() > 0 and self._is_mat_del_row(0):
                self._table.removeRow(0)

    def _is_mat_del_row(self, row: int) -> bool:
        """Check if the given row is the material-delete row."""
        if not self._mat_ids:
            return False
        widget = self._table.cellWidget(row, self.MAT_START)
        if widget is None:
            return False
        btn = widget.findChild(QPushButton)
        return btn is not None and "col" in (btn.text() or "")

    # ── edit mode ──────────────────────────────────────────

    def _toggle_edit(self, checked: bool):
        self._edit_mode = checked
        self._edit_btn.setText("✔ Done" if checked else "✎  Edit")
        self._apply_edit_visibility()
        self._rebuild_mat_delete_row()

    def _apply_edit_visibility(self):
        """Show/hide delete column; toggle chapter name editability."""
        self._table.setColumnHidden(self.COL_DEL, not self._edit_mode)
        for edit in self._chapter_edits:
            edit.setReadOnly(not self._edit_mode)
            edit.setCursor(
                Qt.CursorShape.IBeamCursor if self._edit_mode
                else Qt.CursorShape.ArrowCursor
            )

    # ── actions ────────────────────────────────────────────

    def _on_add_chapter(self):
        dlg = _AddChapterDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, priority = dlg.values()
            if name:
                slm.create_chapter(self.subject.id, name, priority)
                self.refresh()

    def _on_add_material(self):
        if len(self._mat_ids) >= 4:
            QMessageBox.information(self, "Limit Reached", "Maximum 4 material columns allowed.")
            return
        dlg = _AddMaterialDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.value()
            if name:
                slm.create_material(self.subject.id, name)
                self.refresh()

    def _on_priority_changed(self, chapter_id: int, priority: str):
        if self._building:
            return
        slm.update_chapter(chapter_id, priority=priority)
        self.refresh()

    def _delete_chapter(self, chapter_id: int):
        reply = QMessageBox.question(
            self,
            "Delete Chapter",
            "Are you sure you want to delete this chapter? All its progress will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            slm.delete_chapter(chapter_id)
            self.refresh()

    def _delete_material(self, material_id: int):
        reply = QMessageBox.question(
            self,
            "Delete Material Column",
            "Are you sure you want to delete this material column? All associated progress will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            slm.delete_material(material_id)
            self.refresh()

    def _move_material(self, material_id: int, direction: int):
        try:
            idx = self._mat_ids.index(material_id)
            other_idx = idx + direction
            if 0 <= other_idx < len(self._mat_ids):
                other_id = self._mat_ids[other_idx]
                slm.swap_materials(material_id, other_id)
                self.refresh()
        except ValueError:
            pass

    def _update_mat_btn(self):
        self._add_mat_btn.setEnabled(len(self._mat_ids) < 4)


# ─────────────────────────────────────────────────────────────
# Main page
# ─────────────────────────────────────────────────────────────

class SyllabusTrackerPage(QWidget):
    """Syllabus Tracker page — internal nav, per-subject tables, Stats placeholder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Maps subject_id -> SubjectSyllabusPage
        self._subject_pages: dict[int, SubjectSyllabusPage] = {}
        # Maps subject_id -> stack index
        self._subject_stack_idx: dict[int, int] = {}
        self._setup_ui()

    # ── UI setup ────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header bar ──────────────────────────────────────
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(60)
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(20, 0, 20, 0)
        header_lay.setSpacing(12)

        title = QLabel("Syllabus Tracker")
        title.setProperty("class", "heading")
        header_lay.addWidget(title)
        header_lay.addStretch()

        # Page picker dropdown button
        self._picker_btn = QPushButton("Select Subject  ▾")
        self._picker_btn.setObjectName("syllabusPickerBtn")
        self._picker_btn.setProperty("class", "secondary")
        self._picker_btn.clicked.connect(self._show_page_menu)
        header_lay.addWidget(self._picker_btn)

        outer.addWidget(header)

        # Separator
        sep = QFrame()
        sep.setObjectName("headerSeparator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        outer.addWidget(sep)

        # ── Internal stacked area ────────────────────────────
        self._stack = QStackedWidget()
        outer.addWidget(self._stack, stretch=1)

    # ── page navigation ─────────────────────────────────────

    def _show_page_menu(self):
        menu = QMenu(self)
        menu.setObjectName("syllabusMenu")

        subjects = self._get_subjects()
        for subj in subjects:
            act = menu.addAction(f"📖  {subj.name}")
            act.triggered.connect(lambda _, s=subj: self._switch_to_subject(s))

        btn_rect = self._picker_btn.rect()
        pos = self._picker_btn.mapToGlobal(btn_rect.bottomLeft())
        menu.exec(pos)

    def _switch_to(self, idx: int, label: str):
        self._stack.setCurrentIndex(idx)
        self._picker_btn.setText(f"{label}  ▾")

    def _switch_to_subject(self, subj):
        if subj.id not in self._subject_pages:
            self._build_subject_page(subj)
        page = self._subject_pages[subj.id]
        page.subject = subj  # update in case color changed
        page.refresh()
        self._stack.setCurrentIndex(self._subject_stack_idx[subj.id])
        self._picker_btn.setText(f"{subj.name}  ▾")

    def _build_subject_page(self, subj):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = SubjectSyllabusPage(subj)
        scroll.setWidget(page)
        idx = self._stack.addWidget(scroll)
        self._subject_pages[subj.id] = page
        self._subject_stack_idx[subj.id] = idx

    def _get_subjects(self):
        return sm.list_subjects()

    # ── settings gear ───────────────────────────────────────

    def _open_settings(self):
        dlg = _SettingsDialog(self)
        dlg.exec()
        # After closing, rebuild subject pages for any new subjects
        self._sync_subject_pages()

    def _sync_subject_pages(self):
        """Ensure pages exist for all current subjects; clean up deleted ones."""
        subjects = self._get_subjects()
        current_ids = {s.id for s in subjects}

        # Remove pages for deleted subjects
        for sid in list(self._subject_pages.keys()):
            if sid not in current_ids:
                idx = self._subject_stack_idx.pop(sid)
                widget = self._stack.widget(idx)
                self._stack.removeWidget(widget)
                widget.deleteLater()
                del self._subject_pages[sid]
                # Rebuild index map since indices shifted
                self._rebuild_index_map()

        # Pre-build pages for new subjects (optional, lazy is also fine)

    def _rebuild_index_map(self):
        """Rebuild _subject_stack_idx from scratch."""
        new_map = {}
        for sid, page in self._subject_pages.items():
            # Find which stack widget wraps this page's scroll area
            for i in range(self._stack.count()):
                w = self._stack.widget(i)
                if isinstance(w, QScrollArea) and w.widget() is page:
                    new_map[sid] = i
                    break
        self._subject_stack_idx = new_map

    # ── lifecycle ────────────────────────────────────────────

    def refresh(self):
        """Refresh the currently visible subject page (if any)."""
        current = self._stack.currentWidget()
        if isinstance(current, QScrollArea):
            inner = current.widget()
            if isinstance(inner, SubjectSyllabusPage):
                inner.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        # Sync pages every time the page becomes visible (subjects may have changed)
        self._sync_subject_pages()
        
        # Auto-select the first subject if none is selected
        if self._picker_btn.text() == "Select Subject  ▾":
            subjects = self._get_subjects()
            if subjects:
                self._switch_to_subject(subjects[0])
