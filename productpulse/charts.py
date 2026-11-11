"""Chart helpers with one consistent visual system (matches powerbi/theme.json).

Rules followed: one y-axis per chart, thin marks, quiet grid, direct labels,
colour never the only signal (every series is also labelled).
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter

NAVY = "#14243A"
BLUE = "#2563EB"
TEAL = "#0D9488"
AMBER = "#D97706"
VIOLET = "#7C3AED"
MUTED = "#64748B"
GRID = "#E2E8F0"
SURFACE = "#FFFFFF"
CANVAS = "#F5F7FB"

# Fixed order: a category always keeps its colour.
CATEGORICAL = [BLUE, TEAL, AMBER, VIOLET]
DEVICE_COLOURS = {"desktop": BLUE, "mobile": TEAL, "tablet": AMBER}
SEQUENTIAL = LinearSegmentedColormap.from_list("pp_blue", ["#EFF4FF", "#93B4F5", BLUE, "#1E3A8A"])


def _available_font() -> str:
    """Segoe UI on Windows; otherwise the first installed fallback."""
    from matplotlib import font_manager

    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("Segoe UI", "Aptos", "Inter", "Arial", "DejaVu Sans"):
        if name in installed:
            return name
    return "sans-serif"


def apply_style() -> None:
    """Call once at the top of a notebook."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": MUTED,
        "axes.titlecolor": NAVY,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "font.family": _available_font(),
        "font.size": 10,
        "legend.frameon": False,
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
    })


def _thousands(x, _pos=None):
    return f"{x:,.0f}"


def _percent(x, _pos=None):
    return f"{x:.0%}" if x >= 0.1 or x == 0 else f"{x:.1%}"


def note(fig, text: str) -> None:
    """Small caption under a chart: period, unit, caveat."""
    fig.tight_layout()          # pull axis labels inside the figure so the note cannot overlap them
    fig.text(0.01, -0.01, text, ha="left", va="top", fontsize=8.5, color=MUTED, wrap=True)


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, ylabel: str,
               percent: bool = False, rolling: int | None = None, ax=None):
    """Single-series trend line, optionally with a rolling average."""
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=(10, 3.6))
    if rolling:
        ax.plot(df[x], df[y], color=BLUE, linewidth=1, alpha=0.35, label="Daily")
        ax.plot(df[x], df[y].rolling(rolling, min_periods=1).mean(), color=BLUE,
                linewidth=2, label=f"{rolling}-day average")
        ax.legend(loc="lower right", bbox_to_anchor=(1, 1.0), ncol=2, fontsize=9)
    else:
        ax.plot(df[x], df[y], color=BLUE, linewidth=2)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(FuncFormatter(_percent if percent else _thousands))
    return fig, ax


def bar_chart(labels, values, title: str, xlabel: str, percent: bool = False,
              colours=None, ax=None):
    """Horizontal bars with a value label on each bar, largest at the top."""
    labels, values = list(labels), list(values)
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(
        figsize=(8, max(2.2, 0.42 * len(labels) + 1.2)))
    y = np.arange(len(labels))[::-1]
    ax.barh(y, values, color=colours or BLUE, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(FuncFormatter(_percent if percent else _thousands))
    finite = [v for v in values if v == v]
    vmax = max(finite) if finite else 1
    for yi, v in zip(y, values):
        if v == v:
            ax.text(v + vmax * 0.012, yi, f"{v:.1%}" if percent else f"{v:,.0f}",
                    va="center", ha="left", fontsize=9, color=NAVY)
    ax.set_xlim(0, vmax * 1.14 if vmax else 1)
    return fig, ax


def funnel_chart(funnel: pd.DataFrame, count_column: str, title: str, unit: str, ax=None):
    """Funnel drawn as honest horizontal bars: count, % of first stage, step conversion."""
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(figsize=(9, 3.4))
    counts = funnel[count_column].tolist()
    stages = funnel["stage"].tolist()
    y = np.arange(len(stages))[::-1]
    ax.barh(y, counts, color=BLUE, height=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(stages)
    first = counts[0] if counts[0] else float("nan")
    for i, (yi, c) in enumerate(zip(y, counts)):
        label = f"{c:,.0f}  ({c / first:.1%} of first stage)"
        if i > 0 and counts[i - 1]:
            label += f"   step: {c / counts[i - 1]:.1%}"
        ax.text(c + max(counts) * 0.012, yi, label, va="center", ha="left", fontsize=9, color=NAVY)
    ax.set_xlim(0, max(counts) * 1.6 if max(counts) else 1)
    ax.set_title(title)
    ax.set_xlabel(unit)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(FuncFormatter(_thousands))
    return fig, ax


def grouped_rate_chart(df: pd.DataFrame, category: str, rate_columns: dict, title: str, ax=None):
    """Small multiples: one panel per rate, one bar per category (shared colours)."""
    cats = df[category].tolist()
    n = len(rate_columns)
    fig, axes = plt.subplots(1, n, figsize=(3.4 * n, 0.45 * len(cats) + 1.9), sharey=True)
    axes = np.atleast_1d(axes)
    y = np.arange(len(cats))[::-1]
    for ax_i, (col, label) in zip(axes, rate_columns.items()):
        vals = df[col].tolist()
        colours = [DEVICE_COLOURS.get(str(c).lower(), BLUE) for c in cats]
        ax_i.barh(y, vals, color=colours, height=0.6)
        finite = [v for v in vals if v == v]
        vmax = max(finite) if finite else 1
        for yi, v in zip(y, vals):
            if v == v:
                ax_i.text(v + vmax * 0.03, yi, f"{v:.1%}", va="center", fontsize=9, color=NAVY)
        ax_i.set_xlim(0, vmax * 1.3 if vmax else 1)
        ax_i.set_title(label, fontsize=10, fontweight="normal", color=MUTED, pad=6)
        ax_i.xaxis.set_major_formatter(FuncFormatter(_percent))
        ax_i.grid(axis="y", visible=False)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(cats)
    fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold", color=NAVY)
    fig.tight_layout()
    return fig, axes


def cohort_heatmap(matrix: pd.DataFrame, sizes: pd.Series | None, title: str, ax=None):
    """Cohort heatmap. Unobserved periods stay blank (never shown as 0%)."""
    fig, ax = (ax.figure, ax) if ax is not None else plt.subplots(
        figsize=(1.6 * matrix.shape[1] + 3.2, 0.62 * matrix.shape[0] + 1.6))
    data = matrix.to_numpy(dtype=float)
    # Month 0 is always 100%, so scale colour on the later months to keep contrast.
    later = data[:, 1:] if data.shape[1] > 1 else data
    vmax = np.nanmax(later) if np.isfinite(later).any() else 1
    masked = np.ma.masked_invalid(data)
    cmap = SEQUENTIAL.copy()
    cmap.set_bad(CANVAS)
    ax.imshow(masked, cmap=cmap, vmin=0, vmax=max(vmax, 0.01) * 1.15, aspect="auto")
    # Month 0 is 100% by definition: draw it in neutral grey so it does not dominate.
    from matplotlib.patches import Rectangle
    for i in range(data.shape[0]):
        ax.add_patch(Rectangle((-0.5, i - 0.5), 1, 1, facecolor=GRID, edgecolor="none"))
    for edge in np.arange(-0.5, data.shape[0], 1)[1:]:
        ax.axhline(edge, color=SURFACE, linewidth=2)
    for edge in np.arange(-0.5, data.shape[1], 1)[1:]:
        ax.axvline(edge, color=SURFACE, linewidth=2)
    ax.set_xticks(range(matrix.shape[1]))
    ax.set_xticklabels([f"Month {c}" for c in matrix.columns])
    ylabels = list(matrix.index)
    if sizes is not None:
        ylabels = [f"{idx}   (n = {int(sizes.loc[idx]):,})" for idx in matrix.index]
    ax.set_yticks(range(matrix.shape[0]))
    ax.set_yticklabels(ylabels)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            if np.isnan(v):
                ax.text(j, i, "not observed", ha="center", va="center", fontsize=8, color=MUTED)
            else:
                dark = j > 0 and v > vmax * 0.6
                ax.text(j, i, f"{v:.1%}", ha="center", va="center", fontsize=10,
                        color="white" if dark else NAVY)
    ax.set_title(title)
    ax.grid(False)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    return fig, ax


def save_figure(fig, name: str):
    """Save a chart to reports/figures/. Files made from demo data get a DEMO_ prefix."""
    from . import data

    _, is_demo = data.get_data_dir()
    folder = data.ROOT / "reports" / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{'DEMO_' if is_demo else ''}{name}.png"
    fig.savefig(path)
    return path
