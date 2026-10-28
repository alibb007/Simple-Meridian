"""Plotly charts that share the app's tokens (see utils/ui.py).

Every channel keeps one color across every chart (color follows the entity).
"""
from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.ui import BAD, BORDER, FONT_BODY, FONT_DISPLAY, GRID, INK, MUTED, PALETTE, PRIMARY, SURFACE, money

BASELINE = "#B8C2D6"
UP, DOWN = "#2A78D6", "#E34948"  # diverging pair: spend more / spend less

CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}


def color_map(channels) -> dict[str, str]:
    """Fixed slot per channel, in model order. Past 8 channels colors repeat (rare in MMM)."""
    return {str(c): PALETTE[i % len(PALETTE)] for i, c in enumerate(channels)}


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _layout(fig: go.Figure, height: int = 420, legend: bool = False, **kw) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=20, t=36 if legend else 18, b=12),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family=FONT_BODY, color=INK, size=13),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(family=FONT_BODY, color=INK, size=13)),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(color=MUTED)),
        **{"bargap": 0.38, **kw},
    )
    axis = dict(gridcolor=GRID, zeroline=False, linecolor=BORDER, tickfont=dict(color=MUTED, size=12))
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    return fig


def roi_bars(summary: pd.DataFrame, colors: dict) -> go.Figure:
    d = summary[~summary.is_total].sort_values("roi")
    fig = go.Figure(go.Bar(
        x=d.roi, y=d.channel, orientation="h",
        marker=dict(color=[colors[c] for c in d.channel], cornerradius=6),
        error_x=dict(type="data", symmetric=False, array=d.roi_hi - d.roi, arrayminus=d.roi - d.roi_lo,
                     color="#344054", thickness=1.4, width=5),
        customdata=d[["roi_lo", "roi_hi", "spend"]].values,
        hovertemplate="<b>%{y}</b><br>ROI %{x:.2f}<br>90% CI %{customdata[0]:.2f} – %{customdata[1]:.2f}"
                      "<br>Spend $%{customdata[2]:,.0f}<extra></extra>",
    ))
    fig.add_vline(x=1, line=dict(color=BAD, width=1.5, dash="dash"))
    fig.add_annotation(x=1, y=1.04, yref="paper", text="Break-even", showarrow=False,
                       font=dict(color=BAD, size=12), xanchor="left", xshift=4)
    _layout(fig, height=max(320, 58 * len(d) + 70))
    fig.update_xaxes(title=dict(text="Revenue per $1 spent", font=dict(color=MUTED, size=12)), rangemode="tozero")
    fig.update_yaxes(tickfont=dict(color=INK, size=13))
    return fig


def share_bars(summary: pd.DataFrame, colors: dict) -> go.Figure:
    d = summary[~summary.is_total].sort_values("pct_contribution")
    spend_pct = d.pct_spend * (100 if d.pct_spend.max() <= 1 else 1)
    fig = go.Figure()
    fig.add_bar(y=d.channel, x=spend_pct, name="Share of spend", orientation="h",
                marker=dict(color=[_rgba(colors[c], .28) for c in d.channel], cornerradius=6),
                hovertemplate="<b>%{y}</b><br>Share of spend %{x:.1f}%<extra></extra>")
    fig.add_bar(y=d.channel, x=d.pct_contribution, name="Share of media revenue", orientation="h",
                marker=dict(color=[colors[c] for c in d.channel], cornerradius=6),
                hovertemplate="<b>%{y}</b><br>Share of media revenue %{x:.1f}%<extra></extra>")
    # No legend: its swatch would take the first channel's color. The caption explains light vs. solid.
    _layout(fig, height=max(340, 68 * len(d) + 70), barmode="group")
    fig.update_xaxes(ticksuffix="%")
    fig.update_yaxes(tickfont=dict(color=INK, size=13))
    return fig


def contribution_donut(baseline: float, summary: pd.DataFrame, colors: dict) -> go.Figure:
    d = summary[~summary.is_total].sort_values("incremental", ascending=False)
    labels = ["Baseline"] + d.channel.tolist()
    values = [baseline] + d.incremental.tolist()
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62, sort=False, direction="clockwise",
        marker=dict(colors=[BASELINE] + [colors[c] for c in d.channel], line=dict(color=SURFACE, width=2)),
        texttemplate="%{percent:.0%}", textfont=dict(color="#fff", size=12),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    total = sum(values)
    fig.add_annotation(text=f"<b>{money(total)}</b><br><span style='font-size:12px;color:{MUTED}'>modeled revenue</span>",
                       showarrow=False, font=dict(family=FONT_DISPLAY, size=22, color=INK))
    _layout(fig, height=380, legend=True)
    fig.update_layout(legend=dict(orientation="v", x=1.02, y=0.5, yanchor="middle"))
    return fig


def contribution_bars(baseline: float, summary: pd.DataFrame, colors: dict) -> go.Figure:
    d = summary[~summary.is_total].sort_values("incremental", ascending=False)
    fig = go.Figure(go.Bar(
        x=d.channel, y=d.incremental, marker=dict(color=[colors[c] for c in d.channel], cornerradius=6),
        error_y=dict(type="data", symmetric=False, array=d.incremental_hi - d.incremental,
                     arrayminus=d.incremental - d.incremental_lo, color="#344054", thickness=1.4, width=5),
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
    ))
    _layout(fig, height=380)
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    fig.update_xaxes(tickfont=dict(color=INK, size=13))
    return fig


def roi_vs_mroi(summary: pd.DataFrame, colors: dict) -> go.Figure:
    d = summary[~summary.is_total]
    size = 16 + 36 * (d.spend / d.spend.max()) ** 0.5
    fig = go.Figure(go.Scatter(
        x=d.roi, y=d.mroi, mode="markers+text", text=d.channel, textposition="top center",
        textfont=dict(color=INK, size=13),
        marker=dict(size=size, color=[colors[c] for c in d.channel], opacity=0.9, line=dict(color=SURFACE, width=2)),
        customdata=d[["spend"]].values,
        hovertemplate="<b>%{text}</b><br>ROI %{x:.2f}<br>Marginal ROI %{y:.2f}<br>Spend $%{customdata[0]:,.0f}<extra></extra>",
    ))
    fig.add_hline(y=1, line=dict(color=BAD, width=1.5, dash="dash"))
    fig.add_annotation(x=1, xref="paper", y=1, text="Next $1 breaks even", showarrow=False, xanchor="right", yshift=11,
                       font=dict(color=BAD, size=12))
    _layout(fig, height=440)
    fig.update_xaxes(title=dict(text="ROI (average)", font=dict(color=MUTED, size=12)))
    fig.update_yaxes(title=dict(text="Marginal ROI (next dollar)", font=dict(color=MUTED, size=12)))
    return fig


def model_fit(series: pd.DataFrame) -> go.Figure:
    s = series
    fig = go.Figure()
    fig.add_scatter(x=pd.concat([s.time, s.time[::-1]]), y=pd.concat([s.expected_hi, s.expected_lo[::-1]]),
                    fill="toself", fillcolor=_rgba(PRIMARY, .12), line=dict(width=0), hoverinfo="skip",
                    name="90% interval")
    fig.add_scatter(x=s.time, y=s.actual, name="Actual", line=dict(color=INK, width=2),
                    hovertemplate="%{x|%d %b %Y}<br>Actual $%{y:,.0f}<extra></extra>")
    fig.add_scatter(x=s.time, y=s.expected, name="Model", line=dict(color=PRIMARY, width=2),
                    hovertemplate="Model $%{y:,.0f}<extra></extra>")
    fig.add_scatter(x=s.time, y=s.baseline, name="Baseline (no media)", line=dict(color="#98A2B3", width=1.6, dash="dot"),
                    hovertemplate="Baseline $%{y:,.0f}<extra></extra>")
    _layout(fig, height=440, legend=True, hovermode="x unified")
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return fig


def response_grid(curves: pd.DataFrame, colors: dict, show_ci: bool = True,
                  optimized: pd.DataFrame | None = None) -> go.Figure:
    """Small multiples, one panel per channel. Circle = today's spend, diamond = plan."""
    channels = list(dict.fromkeys(curves.channel))
    cols = 3 if len(channels) > 4 else min(2, len(channels))
    rows = math.ceil(len(channels) / cols)
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=[f"<b>{c}</b>" for c in channels],
                        horizontal_spacing=0.07, vertical_spacing=0.17)
    for i, ch in enumerate(channels):
        r, c = i // cols + 1, i % cols + 1
        col = colors.get(ch, PRIMARY)
        d = curves[curves.channel == ch].sort_values("spend")
        if show_ci:
            fig.add_scatter(x=pd.concat([d.spend, d.spend[::-1]]), y=pd.concat([d.hi, d.lo[::-1]]), fill="toself",
                            fillcolor=_rgba(col, .14), line=dict(width=0), hoverinfo="skip", row=r, col=c)
        else:
            fig.add_scatter(x=d.spend, y=d["mean"], fill="tozeroy", fillcolor=_rgba(col, .08), line=dict(width=0),
                            hoverinfo="skip", row=r, col=c)
        fig.add_scatter(x=d.spend, y=d["mean"], line=dict(color=col, width=2.5), row=r, col=c,
                        customdata=d[["multiplier"]].values,
                        hovertemplate=f"<b>{ch}</b><br>Spend $%{{x:,.0f}} (%{{customdata[0]:.0%}} of actual)"
                                      "<br>Incremental $%{y:,.0f}<extra></extra>")
        now = d.iloc[(d.multiplier - 1).abs().argsort().iloc[0]]
        fig.add_vline(x=now.spend, line=dict(color="#98A2B3", width=1, dash="dot"), row=r, col=c)
        fig.add_scatter(x=[now.spend], y=[now["mean"]], mode="markers", row=r, col=c,
                        marker=dict(size=11, color=SURFACE, line=dict(color=col, width=3)),
                        hovertemplate=f"<b>{ch}: actual spend</b><br>$%{{x:,.0f}} → $%{{y:,.0f}}<extra></extra>")
        if optimized is not None:
            o = optimized[optimized.channel == ch]
            if len(o):
                fig.add_scatter(x=o.optimized_spend, y=o.optimized_outcome, mode="markers", row=r, col=c,
                                marker=dict(size=13, symbol="diamond", color=col, line=dict(color=SURFACE, width=2)),
                                hovertemplate=f"<b>{ch}: plan</b><br>$%{{x:,.0f}} → $%{{y:,.0f}}<extra></extra>")
    _layout(fig, height=270 * rows + 40)
    fig.update_annotations(font=dict(family=FONT_BODY, size=14, color=INK))
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return fig


def spend_change(table: pd.DataFrame) -> go.Figure:
    d = table.sort_values("spend_change")
    fig = go.Figure(go.Bar(
        x=d.spend_change, y=d.channel, orientation="h",
        marker=dict(color=[UP if v >= 0 else DOWN for v in d.spend_change], cornerradius=6),
        text=[f"{p:+.0f}%" for p in d.spend_change_pct], textposition="outside",
        textfont=dict(color=INK, size=12),
        customdata=d[["current_spend", "optimized_spend", "spend_change_pct"]].values,
        hovertemplate="<b>%{y}</b><br>$%{customdata[0]:,.0f} → $%{customdata[1]:,.0f}"
                      "<br>%{customdata[2]:+.1f}%<extra></extra>",
    ))
    fig.add_vline(x=0, line=dict(color="#667085", width=1))
    _layout(fig, height=max(320, 58 * len(d) + 70))
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_yaxes(tickfont=dict(color=INK, size=13))
    return fig


def allocation_bars(table: pd.DataFrame, colors: dict) -> go.Figure:
    """Before / after share of budget as two stacked 100% bars."""
    fig = go.Figure()
    for ch in table.channel:
        row = table[table.channel == ch].iloc[0]
        tot_b, tot_a = table.current_spend.sum(), table.optimized_spend.sum()
        fig.add_bar(y=["Plan", "Actual"], x=[row.optimized_spend / tot_a * 100, row.current_spend / tot_b * 100],
                    name=ch, orientation="h", marker=dict(color=colors.get(ch, PRIMARY), line=dict(color=SURFACE, width=2)),
                    hovertemplate=f"<b>{ch}</b><br>%{{y}}: %{{x:.1f}}% of budget<extra></extra>")
    _layout(fig, height=220, legend=True, barmode="stack", legend_traceorder="normal")
    fig.update_xaxes(ticksuffix="%", range=[0, 100])
    fig.update_yaxes(tickfont=dict(color=INK, size=13))
    return fig



# --------------------------------------------------------------------------- #
# Lift test (GeoX)
# --------------------------------------------------------------------------- #
TREATMENT, CONTROL = "#6250D6", "#98A2B3"


def geo_groups(df: pd.DataFrame, treatment: list[str], excluded: list[str] | None = None) -> go.Figure:
    """Average daily revenue per region, colored by group."""
    excluded = set(excluded or [])
    size = df.groupby("location")["conversions"].mean().sort_values(ascending=False)
    groups = ["Test" if g in set(treatment) else ("Left out" if g in excluded else "Control") for g in size.index]
    colors = {"Test": TREATMENT, "Control": CONTROL, "Left out": "#E4E7EC"}
    fig = go.Figure()
    for name in ["Test", "Control", "Left out"]:
        idx = [i for i, g in enumerate(groups) if g == name]
        if idx:
            fig.add_bar(x=size.index[idx], y=size.values[idx], name=name, marker=dict(color=colors[name], cornerradius=4),
                        hovertemplate="<b>%{x}</b><br>avg $%{y:,.0f} per day<extra>" + name + "</extra>")
    _layout(fig, height=300, legend=True, bargap=0.25)
    fig.update_xaxes(categoryorder="array", categoryarray=list(size.index), showticklabels=False, title="Regions, largest first")
    fig.update_yaxes(tickprefix="$", tickformat="~s", title="Avg daily revenue")
    return fig


def geo_counterfactual(cf: pd.DataFrame, start) -> go.Figure:
    """Test regions: what happened vs. what GeoX predicts would have happened without the campaign."""
    d = cf.copy()
    d["date"] = pd.to_datetime(d["date"])
    test = d[d["date"] >= pd.Timestamp(start)]
    fig = go.Figure()
    fig.add_vrect(x0=pd.Timestamp(start), x1=d["date"].max(), fillcolor=_rgba(TREATMENT, .07), line_width=0,
                  annotation_text="Test period", annotation_position="top left",
                  annotation_font=dict(color=TREATMENT, size=12))
    fig.add_scatter(x=pd.concat([test.date, test.date[::-1]]), y=pd.concat([test.upper_bound, test.lower_bound[::-1]]),
                    fill="toself", fillcolor=_rgba(CONTROL, .25), line=dict(width=0), hoverinfo="skip",
                    name="Range without campaign")
    fig.add_scatter(x=d.date, y=d.observed, name="Actual (test regions)", line=dict(color=TREATMENT, width=2),
                    hovertemplate="%{x|%d %b}<br>Actual $%{y:,.0f}<extra></extra>")
    fig.add_scatter(x=d.date, y=d.counterfactual, name="Expected without campaign", line=dict(color="#475467", width=1.8, dash="dot"),
                    hovertemplate="Expected $%{y:,.0f}<extra></extra>")
    _layout(fig, height=380, legend=True, hovermode="x unified")
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return fig


def geo_cumulative(cum: pd.DataFrame) -> go.Figure:
    d = cum.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.dropna(subset=["lift"])
    fig = go.Figure()
    fig.add_scatter(x=pd.concat([d.date, d.date[::-1]]), y=pd.concat([d.upper_bound, d.lower_bound[::-1]]),
                    fill="toself", fillcolor=_rgba(TREATMENT, .15), line=dict(width=0), hoverinfo="skip", name="90% range")
    fig.add_scatter(x=d.date, y=d.lift, name="Extra revenue so far", line=dict(color=TREATMENT, width=2.5),
                    hovertemplate="%{x|%d %b}<br>+$%{y:,.0f}<extra></extra>")
    fig.add_hline(y=0, line=dict(color="#667085", width=1))
    _layout(fig, height=320, legend=True)
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return fig
