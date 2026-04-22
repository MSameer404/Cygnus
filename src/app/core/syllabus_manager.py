# src/app/core/syllabus_manager.py
"""CRUD operations for the Syllabus Tracker (chapters, materials, progress)."""

from sqlmodel import select, delete

from app.data.database import get_session
from app.data.models import (
    PRIORITY_ORDER,
    SyllabusChapter,
    SyllabusMaterial,
    SyllabusProgress,
)

# ──────────────────────────────────────────────────────────────
# Chapters
# ──────────────────────────────────────────────────────────────

def list_chapters(subject_id: int) -> list[SyllabusChapter]:
    """Return all chapters for a subject sorted by priority then sort_order."""
    with get_session() as session:
        stmt = select(SyllabusChapter).where(SyllabusChapter.subject_id == subject_id)
        chapters = list(session.exec(stmt).all())
    # Sort in Python so we can use the PRIORITY_ORDER dict
    chapters.sort(key=lambda c: (PRIORITY_ORDER.get(c.priority, 1), c.sort_order))
    return chapters


def create_chapter(subject_id: int, name: str, priority: str = "Medium") -> SyllabusChapter:
    """Create a new chapter for a subject."""
    with get_session() as session:
        existing = session.exec(
            select(SyllabusChapter)
            .where(SyllabusChapter.subject_id == subject_id)
            .order_by(SyllabusChapter.sort_order.desc())
        ).first()
        next_order = (existing.sort_order + 1) if existing else 0

        chapter = SyllabusChapter(
            subject_id=subject_id,
            name=name.strip(),
            priority=priority,
            sort_order=next_order,
        )
        session.add(chapter)
        session.commit()
        session.refresh(chapter)
        return chapter


def update_chapter(
    chapter_id: int,
    *,
    name: str | None = None,
    priority: str | None = None,
) -> SyllabusChapter | None:
    """Update a chapter's name and/or priority."""
    with get_session() as session:
        chapter = session.get(SyllabusChapter, chapter_id)
        if chapter is None:
            return None
        if name is not None:
            chapter.name = name.strip()
        if priority is not None:
            chapter.priority = priority
        session.add(chapter)
        session.commit()
        session.refresh(chapter)
        return chapter


def delete_chapter(chapter_id: int) -> bool:
    """Delete a chapter and all its progress records."""
    with get_session() as session:
        chapter = session.get(SyllabusChapter, chapter_id)
        if chapter is None:
            return False
        # Delete progress rows first
        session.exec(
            delete(SyllabusProgress).where(SyllabusProgress.chapter_id == chapter_id)
        )
        session.delete(chapter)
        session.commit()
        return True


# ──────────────────────────────────────────────────────────────
# Materials (columns)
# ──────────────────────────────────────────────────────────────

def list_materials(subject_id: int) -> list[SyllabusMaterial]:
    """Return all material columns for a subject sorted by col_index."""
    with get_session() as session:
        stmt = (
            select(SyllabusMaterial)
            .where(SyllabusMaterial.subject_id == subject_id)
            .order_by(SyllabusMaterial.col_index)
        )
        return list(session.exec(stmt).all())


def create_material(subject_id: int, name: str) -> SyllabusMaterial | None:
    """Create a material column. Returns None if 4 columns already exist."""
    with get_session() as session:
        existing = list(
            session.exec(
                select(SyllabusMaterial).where(SyllabusMaterial.subject_id == subject_id)
            ).all()
        )
        if len(existing) >= 4:
            return None
        col_idx = len(existing)
        material = SyllabusMaterial(subject_id=subject_id, name=name.strip(), col_index=col_idx)
        session.add(material)
        session.commit()
        session.refresh(material)
        return material


def delete_material(material_id: int) -> bool:
    """Delete a material column and all its progress records."""
    with get_session() as session:
        material = session.get(SyllabusMaterial, material_id)
        if material is None:
            return False
        subject_id = material.subject_id
        # Delete progress rows first
        session.exec(
            delete(SyllabusProgress).where(SyllabusProgress.material_id == material_id)
        )
        session.delete(material)
        session.commit()

        # Re-index remaining materials for this subject
        remaining = list(
            session.exec(
                select(SyllabusMaterial)
                .where(SyllabusMaterial.subject_id == subject_id)
                .order_by(SyllabusMaterial.col_index)
            ).all()
        )
        for i, mat in enumerate(remaining):
            mat.col_index = i
            session.add(mat)
        session.commit()
        return True


def swap_materials(mat1_id: int, mat2_id: int) -> bool:
    """Swap the col_index of two material columns."""
    with get_session() as session:
        mat1 = session.get(SyllabusMaterial, mat1_id)
        mat2 = session.get(SyllabusMaterial, mat2_id)
        if not mat1 or not mat2:
            return False
        
        # Swap indices
        temp = mat1.col_index
        mat1.col_index = mat2.col_index
        mat2.col_index = temp
        
        session.add(mat1)
        session.add(mat2)
        session.commit()
        return True


# ──────────────────────────────────────────────────────────────
# Progress (checkbox state)
# ──────────────────────────────────────────────────────────────

def get_progress(chapter_id: int, material_id: int) -> bool:
    """Return True if the checkbox for (chapter, material) is checked."""
    with get_session() as session:
        stmt = (
            select(SyllabusProgress)
            .where(
                SyllabusProgress.chapter_id == chapter_id,
                SyllabusProgress.material_id == material_id,
            )
        )
        row = session.exec(stmt).first()
        return row.is_done if row else False


def set_progress(chapter_id: int, material_id: int, is_done: bool) -> None:
    """Set the checkbox state for (chapter, material), creating the row if needed."""
    with get_session() as session:
        stmt = (
            select(SyllabusProgress)
            .where(
                SyllabusProgress.chapter_id == chapter_id,
                SyllabusProgress.material_id == material_id,
            )
        )
        row = session.exec(stmt).first()
        if row is None:
            row = SyllabusProgress(
                chapter_id=chapter_id, material_id=material_id, is_done=is_done
            )
        else:
            row.is_done = is_done
        session.add(row)
        session.commit()


def bulk_get_progress(chapter_ids: list[int], material_ids: list[int]) -> dict[tuple[int, int], bool]:
    """Return a mapping of (chapter_id, material_id) -> is_done for efficient bulk reads."""
    if not chapter_ids or not material_ids:
        return {}
    with get_session() as session:
        stmt = select(SyllabusProgress).where(
            SyllabusProgress.chapter_id.in_(chapter_ids),
            SyllabusProgress.material_id.in_(material_ids),
        )
        rows = session.exec(stmt).all()
    return {(r.chapter_id, r.material_id): r.is_done for r in rows}
