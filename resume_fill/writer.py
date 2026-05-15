import copy
import re
from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import _Cell

from .formatter import format_value
from .loader import flatten_profile
from .matcher import FieldMatcher

_PROJECT_RE = re.compile(r"^projects\.(\d+)\.")

# Horizontal table is only filled when these identifying project fields appear
_IDENTIFYING_PROJECT_FIELDS = {
    "projects.0.name",
    "projects.0.role",
    "projects.0.description",
}


def fill_template(
    template_path: str | Path,
    profile: dict,
    matcher: FieldMatcher,
    output_path: str | Path,
) -> dict[str, int]:
    doc = Document(str(template_path))
    flat = flatten_profile(profile)
    stats = {"filled": 0, "skipped": 0}

    for table in doc.tables:
        rows_cells = [[cell for cell in row.cells] for row in table.rows]
        if _count_table_labels(rows_cells, matcher) < 2:
            continue
        col_map = _build_col_map(rows_cells, matcher)
        if _is_horizontal_table(rows_cells, col_map):
            header_count = _count_header_rows(rows_cells)
            _fill_horizontal(rows_cells[header_count:], col_map, flat, stats)
        else:
            _fill_vertical(rows_cells, flat, matcher, stats)

    doc.save(str(output_path))
    return stats


# ── helpers ──────────────────────────────────────────────────────────────────

def _first_line(text: str) -> str:
    """Use only the first line of a cell for label matching."""
    return text.split("\n")[0].strip()


def _count_table_labels(rows_cells: list[list[_Cell]], matcher: FieldMatcher) -> int:
    """Count distinct label cells across the entire table."""
    seen: set[int] = set()
    count = 0
    for row_cells in rows_cells:
        for _, cell in _unique_cells(row_cells, seen):
            if matcher.match(_first_line(cell.text)) is not None:
                count += 1
    return count


def _unique_cells(cells: list[_Cell], seen: set) -> list[tuple[int, _Cell]]:
    """Yield (col_idx, cell) for cells not already in seen (by _tc id)."""
    result = []
    for c_idx, cell in enumerate(cells):
        cid = id(cell._tc)
        if cid not in seen:
            seen.add(cid)
            result.append((c_idx, cell))
    return result


def _row_is_empty(cells: list[_Cell], seen: set | None = None) -> bool:
    if seen is None:
        seen = set()
    for _, cell in _unique_cells(cells, seen):
        if cell.text.strip():
            return False
    return True


# ── horizontal table handling ─────────────────────────────────────────────────

def _build_col_map(rows_cells: list[list[_Cell]], matcher: FieldMatcher) -> dict[int, str]:
    """Scan first 2 rows and map col_idx → field_key for any matching labels."""
    seen: set[int] = set()
    col_map: dict[int, str] = {}
    for row_cells in rows_cells[:2]:
        for c_idx, cell in _unique_cells(row_cells, seen):
            fk = matcher.match(_first_line(cell.text))
            if fk is not None and c_idx not in col_map:
                col_map[c_idx] = fk
    return col_map


def _is_horizontal_table(rows_cells: list[list[_Cell]], col_map: dict[int, str]) -> bool:
    """
    Horizontal table: ≥ 3 distinct label columns in first 2 rows AND
    at least one identifying project field AND at least one all-empty data row.
    """
    if len(col_map) < 3:
        return False
    if not any(v in _IDENTIFYING_PROJECT_FIELDS for v in col_map.values()):
        return False
    # Verify at least one completely empty data row exists (below row index 1)
    for row_cells in rows_cells[2:]:
        if _row_is_empty(row_cells):
            return True
    return False


def _count_header_rows(rows_cells: list[list[_Cell]]) -> int:
    """Count leading rows where every unique cell has text (no empty cells)."""
    for row_idx, cells in enumerate(rows_cells):
        seen: set[int] = set()
        for _, cell in _unique_cells(cells, seen):
            if not cell.text.strip():
                return row_idx
    return len(rows_cells)


def _fill_horizontal(
    data_rows: list[list[_Cell]],
    col_map: dict[int, str],
    flat: dict[str, Any],
    stats: dict,
) -> None:
    max_projects = _project_count(flat)
    project_idx = 0

    for row_cells in data_rows:
        if project_idx >= max_projects:
            break
        if not _row_is_empty(row_cells):
            continue

        for c_idx, base_key in col_map.items():
            if c_idx >= len(row_cells):
                continue
            cell = row_cells[c_idx]
            eff_key = _reindex_project_key(base_key, project_idx)
            value = flat.get(eff_key)
            if value is None:
                stats["skipped"] += 1
                continue
            formatted = format_value(value, eff_key)
            if formatted:
                _set_cell_text(cell, formatted)
                stats["filled"] += 1

        project_idx += 1


def _reindex_project_key(key: str, idx: int) -> str:
    return _PROJECT_RE.sub(f"projects.{idx}.", key)


def _project_count(flat: dict) -> int:
    max_idx = -1
    for k in flat:
        m = _PROJECT_RE.match(k)
        if m:
            max_idx = max(max_idx, int(m.group(1)))
    return max_idx + 1 if max_idx >= 0 else 0


# ── vertical table handling ───────────────────────────────────────────────────

def _label_count_in_row(cells: list[_Cell], matcher: FieldMatcher) -> int:
    """Count unique cells that match a label (for header-row detection)."""
    seen: set[int] = set()
    count = 0
    for _, cell in _unique_cells(cells, seen):
        if matcher.match(_first_line(cell.text)) is not None:
            count += 1
    return count


def _fill_vertical(
    rows_cells: list[list[_Cell]],
    flat: dict[str, Any],
    matcher: FieldMatcher,
    stats: dict,
) -> None:
    visited: set[int] = set()

    for row_idx, cells in enumerate(rows_cells):
        # Rows with ≥ 3 label cells are column-header rows, not key-value rows.
        # Treating their labels as row-labels would fill adjacent/below cells incorrectly.
        if _label_count_in_row(cells, matcher) >= 3:
            continue

        for col_idx, cell in enumerate(cells):
            cell_id = id(cell._tc)
            if cell_id in visited:
                continue
            visited.add(cell_id)

            label = _first_line(cell.text)
            field_key = matcher.match(label)
            if field_key is None:
                continue

            value_cell = _find_value_cell(rows_cells, row_idx, col_idx, visited, matcher)
            if value_cell is None:
                stats["skipped"] += 1
                continue

            value = flat.get(field_key)
            if value is None:
                stats["skipped"] += 1
                continue

            formatted = format_value(value, field_key)
            if formatted:
                _set_cell_text(value_cell, formatted)
                visited.add(id(value_cell._tc))
                stats["filled"] += 1


def _find_value_cell(
    rows_cells: list[list[_Cell]],
    row_idx: int,
    col_idx: int,
    visited: set,
    matcher: FieldMatcher,
) -> _Cell | None:
    cells = rows_cells[row_idx]
    current_tc_id = id(cells[col_idx]._tc)

    for next_col in range(col_idx + 1, len(cells)):
        candidate = cells[next_col]
        cid = id(candidate._tc)
        if cid == current_tc_id:
            continue
        if cid in visited:
            continue
        candidate_text = candidate.text.strip()
        if candidate_text:
            # Non-empty: stop scanning if it's a label; skip (don't overwrite) otherwise
            if matcher.match(_first_line(candidate_text)) is not None:
                break
            continue
        return candidate  # Empty cell → use as value target

    # Fallback: cell directly below (only if it's empty)
    if row_idx + 1 < len(rows_cells) and col_idx < len(rows_cells[row_idx + 1]):
        below = rows_cells[row_idx + 1][col_idx]
        bid = id(below._tc)
        if bid not in visited and bid != current_tc_id and not below.text.strip():
            return below

    return None


# ── cell text writing ─────────────────────────────────────────────────────────

def _set_cell_text(cell: _Cell, text: str) -> None:
    if not cell.paragraphs:
        return

    para = cell.paragraphs[0]

    existing_rpr = None
    if para.runs:
        rpr_elem = para.runs[0]._element.find(qn("w:rPr"))
        if rpr_elem is not None:
            existing_rpr = copy.deepcopy(rpr_elem)

    for r_elem in para._element.findall(qn("w:r")):
        para._element.remove(r_elem)

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if i > 0:
            br_run = OxmlElement("w:r")
            if existing_rpr is not None:
                br_run.append(copy.deepcopy(existing_rpr))
            br_run.append(OxmlElement("w:br"))
            para._element.append(br_run)

        if line:
            r_elem = OxmlElement("w:r")
            if existing_rpr is not None:
                r_elem.append(copy.deepcopy(existing_rpr))
            t_elem = OxmlElement("w:t")
            t_elem.text = line
            if line.startswith(" ") or line.endswith(" "):
                t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            r_elem.append(t_elem)
            para._element.append(r_elem)
