"""Mise en forme des données, tableaux et messages de Personal Framework CLI.

Ce module isole la présentation visuelle (tableaux, unités, badges)
de la logique de diagnostic réseau et de collecte d'informations.
"""

from typing import Optional

from config.settings import (
    COLOR_BOLD,
    COLOR_CYAN,
    COLOR_DIM,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_RESET,
    COLOR_YELLOW,
)


def format_bytes(size_in_bytes: float) -> str:
    """Formate une taille en octets en unité lisible (B, KB, MB, GB).

    Args:
        size_in_bytes: Nombre d'octets.

    Returns:
        Chaîne formatée avec 2 décimales.
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_in_bytes)
    unit_idx = 0

    while value >= 1024.0 and unit_idx < len(units) - 1:
        value /= 1024.0
        unit_idx += 1

    return f"{value:.2f} {units[unit_idx]}" if unit_idx > 0 else f"{int(value)} B"


def format_latency(ms: Optional[float]) -> str:
    """Formate un délai ou RTT en millisecondes ou secondes avec unité."""
    if ms is None:
        return "N/A"
    if ms < 1.0:
        return f"{ms * 1000.0:.0f} µs"
    if ms >= 1000.0:
        return f"{ms / 1000.0:.2f} s"
    return f"{ms:.2f} ms"


def format_badge(state: str) -> str:
    """Génère un badge stylisé en couleurs ANSI selon l'état réseau observé."""
    state_normalized = state.strip().lower()

    if state_normalized in ("open", "ouvert", "up", "reachable", "success"):
        return f"{COLOR_GREEN}{COLOR_BOLD}[ {state.upper()} ]{COLOR_RESET}"
    if state_normalized in ("closed", "fermé", "down", "unreachable"):
        return f"{COLOR_YELLOW}[ {state.upper()} ]{COLOR_RESET}"
    if state_normalized in ("filtered", "filtré", "timeout"):
        return f"{COLOR_RED}[ {state.upper()} ]{COLOR_RESET}"

    return f"{COLOR_DIM}[ {state.upper()} ]{COLOR_RESET}"


def format_table(
    headers: list[str],
    rows: list[list[str]],
    title: Optional[str] = None,
) -> str:
    """Construit un tableau textuel aligné et lisible.

    Args:
        headers: Noms des colonnes.
        rows: Lignes de données (chaque ligne doit avoir la même longueur que headers).
        title: Titre optionnel au-dessus du tableau.

    Returns:
        Chaîne représentant le tableau mis en page.
    """
    if not headers:
        return ""

    # Calcul des largeurs optimales de chaque colonne
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            if idx < len(col_widths):
                col_widths[idx] = max(col_widths[idx], len(str(cell)))

    # Bordures et séparateurs
    header_line = "  ".join(
        f"{COLOR_BOLD}{headers[i]:<{col_widths[i]}}{COLOR_RESET}" for i in range(len(headers))
    )
    separator = "  ".join("-" * col_widths[i] for i in range(len(headers)))

    lines: list[str] = []
    if title:
        lines.append(f"\n{COLOR_CYAN}{COLOR_BOLD}=== {title} ==={COLOR_RESET}")

    lines.append(header_line)
    lines.append(separator)

    for row in rows:
        formatted_row = []
        for i, cell in enumerate(row):
            width = col_widths[i] if i < len(col_widths) else len(cell)
            formatted_row.append(f"{str(cell):<{width}}")
        lines.append("  ".join(formatted_row))

    return "\n".join(lines)
