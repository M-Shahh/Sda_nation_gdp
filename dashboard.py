"""
Dashboard / Presentation Layer Module
======================================
Single Responsibility: Displaying configuration info, computed results,
and generating all visualizations (charts/graphs).

This module does NOT load data or compute statistics — it only presents
the results it receives.

Chart requirements fulfilled:
  - Region-wise GDP: Pie chart + Bar chart  (2 chart types)
  - Year-specific GDP: Line graph + Scatter plot  (2 chart types)
  - All charts are clearly labelled (title, axes/labels).
"""

import matplotlib
matplotlib.use("TkAgg")  # Use interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Rectangle
import numpy as np


# ──────────────────────────────────────────────
#  Utility Helpers
# ──────────────────────────────────────────────

def _format_gdp(value):
    """Format a GDP value into a human-readable string (trillions/billions)."""
    if abs(value) >= 1e12:
        return f"${value / 1e12:,.2f}T"
    elif abs(value) >= 1e9:
        return f"${value / 1e9:,.2f}B"
    elif abs(value) >= 1e6:
        return f"${value / 1e6:,.2f}M"
    return f"${value:,.2f}"


def _trillion_formatter(x, _pos):
    """Matplotlib tick formatter that displays values in trillions."""
    return f"${x / 1e12:.1f}T"


# ──────────────────────────────────────────────
#  Console Summary
# ──────────────────────────────────────────────

def print_summary(results):
    """
    Print a textual summary of the configuration and computed stats.

    Parameters:
        results (dict): Output from data_processor.process_data().
    """
    cfg = results["config_summary"]
    
    # ANSI color codes for enhanced terminal output
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    print("\n" + BLUE + "═" * 60 + RESET)
    print(BOLD + CYAN + f"  {'🌍 World Bank GDP Analysis Dashboard':^56}" + RESET)
    print(BLUE + "═" * 60 + RESET)
    print(f"  {BOLD}Region{RESET}   : {GREEN}{cfg['region']}{RESET}")
    print(f"  {BOLD}Year{RESET}     : {GREEN}{cfg['year']}{RESET}")
    print(f"  {BOLD}Operation{RESET}: {GREEN}{cfg['operation'].capitalize()}{RESET}")
    print(f"  {BOLD}Output{RESET}   : {GREEN}{cfg['output'].capitalize()}{RESET}")
    print(BLUE + "─" * 60 + RESET)
    print(f"  {YELLOW}📊 Data Coverage:{RESET}")
    print(f"     • Region matches : {CYAN}{results['filtered_region_count']:,}{RESET} rows")
    print(f"     • Year matches   : {CYAN}{results['filtered_year_count']:,}{RESET} rows")
    print(BLUE + "─" * 60 + RESET)

    op_label = cfg["operation"].capitalize()
    print(f"\n  {BOLD}💰 {op_label} GDP for '{cfg['region']}' ({cfg['year']}){RESET}")
    print(f"     {GREEN}{_format_gdp(results['region_stat'])}{RESET}")
    print(BLUE + "─" * 60 + RESET)

    print(f"\n  {BOLD}🌏 Region-wise {op_label} GDP (Year {cfg['year']}){RESET}")
    # Use dict comprehension for sorted display
    sorted_regions = dict(sorted(
        results["region_stats_by_year"].items(),
        key=lambda item: item[1],
        reverse=True,
    ))
    _ = list(map(
        lambda item: print(f"     • {item[0]:<30} {CYAN}{_format_gdp(item[1])}{RESET}"),
        sorted_regions.items(),
    ))

    print(f"\n  {BOLD}🏆 Top Countries in {cfg['region']} ({cfg['year']}){RESET}")
    _ = list(map(
        lambda item: print(f"     • {item[0]:<30} {GREEN}{_format_gdp(item[1])}{RESET}"),
        results["top_countries_in_region"].items(),
    ))

    print(f"\n  {BOLD}📈 {cfg['region']} GDP Trend (Recent Years){RESET}")
    # Show last 10 years for brevity
    recent_trend = dict(list(results["region_trend"].items())[-10:])
    _ = list(map(
        lambda item: print(f"     {item[0]}  →  {YELLOW}{_format_gdp(item[1])}{RESET}"),
        recent_trend.items(),
    ))

    print(BLUE + "═" * 60 + RESET + "\n")


# ──────────────────────────────────────────────
#  Chart: Region-wise GDP — PIE CHART
# ──────────────────────────────────────────────

def plot_region_pie_chart(results, ax):
    """
    Draw a pie chart of region-wise GDP for the configured year.

    Parameters:
        results (dict): Processed results.
        ax (matplotlib.axes.Axes): Subplot axes to draw on.
    """
    cfg = results["config_summary"]
    region_data = results["region_stats_by_year"]

    labels = list(region_data.keys())
    sizes = list(region_data.values())

    # Modern color palette with gradients
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE']
    
    # Create pie chart with enhanced styling
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(labels)],
        textprops={"fontsize": 9, "weight": "bold"},
        explode=[0.05 if l == cfg['region'] else 0 for l in labels],  # Explode selected region
        shadow=True,
        wedgeprops={"edgecolor": "white", "linewidth": 2, "antialiased": True}
    )
    
    # Style the percentage text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(8)
        autotext.set_weight('bold')
    
    ax.set_title(
        f"🥧 Region-wise {cfg['operation'].capitalize()} GDP — {cfg['year']}",
        fontsize=12,
        fontweight="bold",
        pad=20,
        color="#2C3E50"
    )


# ──────────────────────────────────────────────
#  Chart: Region-wise GDP — BAR CHART
# ──────────────────────────────────────────────

def plot_region_bar_chart(results, ax):
    """
    Draw a bar chart of region-wise GDP for the configured year.

    Parameters:
        results (dict): Processed results.
        ax (matplotlib.axes.Axes): Subplot axes to draw on.
    """
    cfg = results["config_summary"]
    region_data = results["region_stats_by_year"]

    # Sort regions by GDP descending using sorted + lambda
    sorted_items = sorted(region_data.items(), key=lambda x: x[1], reverse=True)
    labels = list(map(lambda x: x[0], sorted_items))
    values = list(map(lambda x: x[1], sorted_items))

    # Gradient color scheme from dark to light
    colors = ['#1A237E', '#283593', '#3949AB', '#5C6BC0', '#7986CB', '#9FA8DA', '#C5CAE9']
    bar_colors = [colors[i % len(colors)] if labels[i] != cfg['region'] 
                  else '#FF6B6B' for i in range(len(labels))]

    bars = ax.bar(labels, values, color=bar_colors, edgecolor="white", linewidth=2,
                   alpha=0.9, width=0.7)
    
    # Add gradient effect
    for bar in bars:
        bar.set_linewidth(2)
        bar.set_edgecolor('#2C3E50')
    
    ax.set_title(
        f"📊 Region-wise {cfg['operation'].capitalize()} GDP — {cfg['year']}",
        fontsize=12,
        fontweight="bold",
        pad=20,
        color="#2C3E50"
    )
    ax.set_xlabel("Region", fontsize=10, fontweight="bold", color="#34495E")
    ax.set_ylabel("GDP (USD)", fontsize=10, fontweight="bold", color="#34495E")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_trillion_formatter))
    ax.tick_params(axis="x", rotation=35, labelsize=8, colors="#34495E")
    ax.tick_params(axis="y", labelsize=9, colors="#34495E")
    ax.set_facecolor('#F8F9FA')
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.7)

    # Add value labels on bars
    _ = list(map(
        lambda bar: ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            _format_gdp(bar.get_height()),
            ha="center", va="bottom", fontsize=7,
        ),
        bars,
    ))


# ──────────────────────────────────────────────
#  Chart: Year-wise GDP — LINE GRAPH
# ──────────────────────────────────────────────

def plot_year_line_chart(results, ax):
    """
    Draw a line graph of year-wise global GDP.

    Parameters:
        results (dict): Processed results.
        ax (matplotlib.axes.Axes): Subplot axes to draw on.
    """
    cfg = results["config_summary"]
    year_data = results["year_stats_global"]

    years = list(year_data.keys())
    values = list(year_data.values())

    # Main line with gradient effect
    ax.plot(years, values, marker="o", linewidth=3, color="#3498DB", 
            label="Global GDP", markersize=6, markerfacecolor="#E74C3C",
            markeredgecolor="white", markeredgewidth=2, alpha=0.9)
    
    # Gradient fill
    ax.fill_between(years, values, alpha=0.3, color="#3498DB")
    
    # Highlight the selected year
    if cfg['year'] in years:
        idx = years.index(cfg['year'])
        ax.plot(cfg['year'], values[idx], marker="*", markersize=20, 
                color="#F39C12", markeredgecolor="white", markeredgewidth=2,
                label=f"Selected Year ({cfg['year']})")
    
    ax.set_title(
        f"📈 Year-wise Global {cfg['operation'].capitalize()} GDP Trend",
        fontsize=12,
        fontweight="bold",
        pad=20,
        color="#2C3E50"
    )
    ax.set_xlabel("Year", fontsize=10, fontweight="bold", color="#34495E")
    ax.set_ylabel("GDP (USD)", fontsize=10, fontweight="bold", color="#34495E")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_trillion_formatter))
    ax.legend(fontsize=9, loc='upper left', framealpha=0.9, edgecolor='#BDC3C7')
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_facecolor('#F8F9FA')
    ax.tick_params(colors="#34495E")
    
    # Rotate x-axis labels if too many years
    if len(years) > 30:
        ax.tick_params(axis='x', rotation=45, labelsize=7)


# ──────────────────────────────────────────────
#  Chart: Country GDP Trend — SCATTER PLOT
# ──────────────────────────────────────────────

def plot_region_trend_line(results, ax):
    """
    Draw a line plot of the selected region's GDP trend over years.

    Parameters:
        results (dict): Processed results.
        ax (matplotlib.axes.Axes): Subplot axes to draw on.
    """
    cfg = results["config_summary"]
    trend = results["region_trend"]

    if not trend:
        ax.text(0.5, 0.5, "📭 No trend data", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="#7F8C8D")
        ax.set_title("No Data", fontsize=11)
        ax.set_facecolor('#F8F9FA')
        return

    years = list(trend.keys())
    values = list(trend.values())

    # Create gradient for scatter points
    colors_gradient = plt.cm.viridis(np.linspace(0, 1, len(years)))
    
    # Plot with enhanced styling
    ax.scatter(years, values, s=120, c=colors_gradient, edgecolors="white", 
               linewidths=2, zorder=5, alpha=0.9)
    ax.plot(years, values, linestyle="-", color="#8E44AD", alpha=0.6, 
            linewidth=3, label=cfg['region'])
    
    # Add fill for visual effect
    ax.fill_between(years, values, alpha=0.2, color="#8E44AD")
    
    # Highlight selected year
    if cfg['year'] in years:
        idx = years.index(cfg['year'])
        ax.scatter(cfg['year'], values[idx], s=300, marker="*", 
                   color="#F39C12", edgecolors="white", linewidths=2, 
                   zorder=10, label=f"Year {cfg['year']}")
    
    ax.set_title(
        f"📉 {cfg['region']} GDP Trend ({cfg['operation'].capitalize()})",
        fontsize=12,
        fontweight="bold",
        pad=20,
        color="#2C3E50"
    )
    ax.set_xlabel("Year", fontsize=10, fontweight="bold", color="#34495E")
    ax.set_ylabel(f"GDP (USD)", fontsize=10, fontweight="bold", color="#34495E")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_trillion_formatter))
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_facecolor('#F8F9FA')
    ax.tick_params(colors="#34495E")
    ax.legend(fontsize=9, loc='best', framealpha=0.9, edgecolor='#BDC3C7')
    
    # Rotate x-axis labels if too many years
    if len(years) > 20:
        ax.tick_params(axis="x", rotation=45, labelsize=7)


# ──────────────────────────────────────────────
#  Chart: Countries in Region for Year — HORIZONTAL BAR
# ──────────────────────────────────────────────

def plot_region_countries_hbar(results, ax):
    """
    Draw a horizontal bar chart of countries within the selected region
    for the configured year.

    Parameters:
        results (dict): Processed results.
        ax (matplotlib.axes.Axes): Subplot axes to draw on.
    """
    cfg = results["config_summary"]
    country_data = results["region_year_countries"]

    if not country_data:
        ax.text(0.5, 0.5, "📭 No data available", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="#7F8C8D")
        ax.set_title("No Data", fontsize=11)
        ax.set_facecolor('#F8F9FA')
        return

    # Show top 10 countries only for better visibility
    sorted_items = sorted(country_data.items(), key=lambda x: x[1], reverse=True)[:10]
    countries = list(map(lambda x: x[0], sorted_items))
    values = list(map(lambda x: x[1], sorted_items))

    # Gradient color scheme
    colors = ['#E74C3C', '#E67E22', '#F39C12', '#F1C40F', '#2ECC71', 
              '#1ABC9C', '#3498DB', '#9B59B6', '#34495E', '#95A5A6']
    bar_colors = [colors[i] for i in range(len(countries))]

    bars = ax.barh(countries, values, color=bar_colors, edgecolor="white", 
                    linewidth=2, alpha=0.85, height=0.7)
    
    ax.set_title(
        f"🌍 Top Countries in {cfg['region']} — GDP {cfg['year']}",
        fontsize=12,
        fontweight="bold",
        pad=20,
        color="#2C3E50"
    )
    ax.set_xlabel("GDP (USD)", fontsize=10, fontweight="bold", color="#34495E")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_trillion_formatter))
    ax.tick_params(axis='y', labelsize=8, colors="#34495E")
    ax.tick_params(axis='x', labelsize=9, colors="#34495E")
    ax.set_facecolor('#F8F9FA')
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.7)
    ax.invert_yaxis()  # Highest value at top

    _ = list(map(
        lambda bar: ax.text(
            bar.get_width(),
            bar.get_y() + bar.get_height() / 2,
            f" {_format_gdp(bar.get_width())}",
            ha="left", va="center", fontsize=8,
        ),
        bars,
    ))


# ──────────────────────────────────────────────
#  Main Dashboard Renderer
# ──────────────────────────────────────────────

def render_dashboard(results):
    """
    Render the full dashboard: print summary + show all charts.

    Parameters:
        results (dict): Output from data_processor.process_data().
    """
    # 1) Print textual summary to console
    print_summary(results)

    # 2) Set style safely
    style = "seaborn-v0_8-whitegrid"
    available_styles = plt.style.available
    if style in available_styles:
        plt.style.use(style)

    # 3) Create subplot grid (2 rows × 3 cols) with enhanced styling
    fig_size = (18, 11)
    fig, axes = plt.subplots(2, 3, figsize=fig_size)
    fig.patch.set_facecolor('#FFFFFF')
    
    # Enhanced title with gradient background effect
    fig.suptitle(
        "🌍 World Bank GDP Analysis Dashboard",
        fontsize=18,
        fontweight="bold",
        y=0.97,
        color="#2C3E50",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#ECF0F1", 
                  edgecolor="#3498DB", linewidth=2, alpha=0.8)
    )

    # Row 1: Region-wise charts + countries-in-region bar
    plot_region_pie_chart(results, axes[0, 0])
    plot_region_bar_chart(results, axes[0, 1])
    plot_region_countries_hbar(results, axes[0, 2])

    # Row 2: Year-wise charts + region trend + info card
    plot_year_line_chart(results, axes[1, 0])
    plot_region_trend_line(results, axes[1, 1])

    # Info summary card in last subplot
    _draw_info_card(results, axes[1, 2])

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


def _draw_info_card(results, ax):
    """Draw a text-based info card summarising key numbers."""
    cfg = results["config_summary"]
    ax.axis("off")

    # Get top country in region
    top_countries = results.get("top_countries_in_region", {})
    top_country = list(top_countries.keys())[0] if top_countries else "N/A"
    top_country_gdp = list(top_countries.values())[0] if top_countries else 0

    # Create styled info card with colors
    info_lines = [
        "📊 Dashboard Summary",
        "═" * 38,
        "",
        "🌍 Configuration",
        "─" * 38,
        f"  Region     : {cfg['region']}",
        f"  Year       : {cfg['year']}",
        f"  Operation  : {cfg['operation'].capitalize()}",
        f"  Output     : {cfg['output'].capitalize()}",
        "",
        f"💰 {cfg['operation'].capitalize()} GDP",
        "─" * 38,
        f"  {cfg['region']} ({cfg['year']})",
        f"  {_format_gdp(results['region_stat'])}",
        "",
        "🏆 Top Country",
        "─" * 38,
        f"  {top_country[:30]}",
        f"  {_format_gdp(top_country_gdp)}",
        "",
        "📈 Data Coverage",
        "─" * 38,
        f"  Region: {results['filtered_region_count']:,} rows",
        f"  Year:   {results['filtered_year_count']:,} rows",
    ]
    text = "\n".join(info_lines)

    ax.text(
        0.5, 0.5, text,
        transform=ax.transAxes,
        fontsize=9.5,
        verticalalignment="center",
        horizontalalignment="center",
        fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=1", facecolor="#ECF0F1", 
                  edgecolor="#3498DB", linewidth=3, alpha=0.95),
        color="#2C3E50"
    )
    ax.set_title("📋 Summary Card", fontsize=12, fontweight="bold", 
                 pad=20, color="#2C3E50")


def display_error(message):
    """
    Display an error message on the dashboard (simple fallback).

    Parameters:
        message (str): Error message to display.
    """
    print("\n" + "!" * 60)
    print(f"  ERROR: {message}")
    print("!" * 60 + "\n")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    ax.text(
        0.5, 0.5,
        f"⚠ Error\n\n{message}",
        ha="center", va="center",
        fontsize=14, color="red",
        transform=ax.transAxes,
        bbox=dict(boxstyle="round,pad=1", facecolor="#ffe0e0"),
    )
    fig.suptitle("GDP Dashboard — Error", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.show()
