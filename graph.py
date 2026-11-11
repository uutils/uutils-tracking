# This file is part of the uutils tracking project.
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

"""Plot the evolution of a testsuite run against a uutils project.

The input is a date-keyed JSON file, one entry per run:

    {"<RFC 2822 date>": {"sha": ..., "total": N, "pass": N, "fail": N,
                         "skip": N[, "error": N]}, ...}
"""

import argparse

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from graph_common import (
    COLORS,
    add_reference_lines,
    add_title,
    apply_smoothing,
    setup_theme,
    style_axes,
    style_legend,
)

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("json_file", help="date-keyed result file, e.g. gnu-result.json")
parser.add_argument("title", help="name of the testsuite, e.g. GNU")
parser.add_argument("--project", required=True, help="uutils project, e.g. sed")
parser.add_argument(
    "--output", help="SVG file to write (default: <title in lowercase>-results.svg)"
)
args = parser.parse_args()

title = args.title
output = args.output or f"{title.lower()}-results.svg"

d = pd.read_json(args.json_file, orient="index")
df = pd.DataFrame(d)

df.columns.names = ["date"]
df.index = pd.to_datetime(df.index, utc=True)
df = df.sort_index()

print(df)

# Set up modern theme
setup_theme()

# Create figure with better proportions and higher DPI
fig, ax = plt.subplots(figsize=(18, 9), dpi=100)

# Prepare data for plotting - melt to long format for Seaborn
plot_columns = ["total", "pass", "fail"]
if "error" in df.columns and df["error"].notna().any():
    plot_columns.append("error")
plot_columns.append("skip")

df_plot = df[plot_columns].copy()
df_plot = df_plot.reset_index()
df_plot.rename(columns={df_plot.columns[0]: "date"}, inplace=True)
df_plot_long = df_plot.melt(id_vars="date", var_name="metric", value_name="count")

# Convert string values to numeric
df_plot_long["count"] = pd.to_numeric(df_plot_long["count"], errors="coerce")

# Apply smoothing using rolling average (window of 15 for smoother lines)
df_plot_long["count_smooth"] = apply_smoothing(df_plot_long, "metric", "count")

# Use color palette from common module
palette = {k: COLORS[k] for k in plot_columns}

# Add gradient-like area fills first (behind lines)
# Use the smoothed values so the fill follows below the plotted line
smooth_by_metric = df_plot_long.pivot_table(
    index="date", columns="metric", values="count_smooth"
)
for metric in ["total", "pass", "fail"]:
    if metric in smooth_by_metric.columns:
        ax.fill_between(
            smooth_by_metric.index,
            0,
            smooth_by_metric[metric],
            alpha=0.18,
            color=palette[metric],
            zorder=1,
            linewidth=0,
        )

# Use Seaborn's lineplot with enhanced styling and smoothed data
sns.lineplot(
    data=df_plot_long,
    x="date",
    y="count_smooth",
    hue="metric",
    palette=palette,
    linewidth=3.5,
    ax=ax,
    markers=False,  # Disable markers for smoother look
    dashes=False,
    alpha=1,
    zorder=3,
)

# Add title and subtitle
add_title(
    ax,
    f"uutils {args.project} — {title} Test Suite Results",
    "Tracking test results over time to measure progress and compatibility",
)

# Style axes with labels and grid
style_axes(ax, xlabel="Date", ylabel="Number of Tests")

# Add reference lines
y_max = df_plot_long["count_smooth"].max()
add_reference_lines(ax, y_max)

# Style legend
handles, labels = ax.get_legend_handles_labels()
labels = [label.capitalize() for label in labels]
style_legend(ax, handles, labels, ncol=len(plot_columns), loc="upper left")

# Add percentage box on the top right
latest_data = df.iloc[-1]
total = pd.to_numeric(latest_data["total"], errors="coerce")
pass_count = pd.to_numeric(latest_data["pass"], errors="coerce")
fail_count = pd.to_numeric(latest_data["fail"], errors="coerce")
skip_count = pd.to_numeric(latest_data["skip"], errors="coerce")

pass_pct = (pass_count / total) * 100 if total > 0 else 0
fail_pct = (fail_count / total) * 100 if total > 0 else 0
skip_pct = (skip_count / total) * 100 if total > 0 else 0

# Create text box
textstr = "Latest Results:\n"
textstr += f"Pass: {pass_pct:.1f}%\n"
textstr += f"Fail: {fail_pct:.1f}%\n"
textstr += f"Skip: {skip_pct:.1f}%"

# Add text box on the top right
props = {
    "boxstyle": "round,pad=0.8",
    "facecolor": "#FFFFFF",
    "edgecolor": "#D1D5DB",
    "linewidth": 2,
    "alpha": 0.95,
}
ax.text(
    0.98,
    1.15,
    textstr,
    transform=ax.transAxes,
    fontsize=14,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=props,
    color="#374151",
    fontweight="600",
    zorder=10,
)

# Tight layout
plt.tight_layout()

# Save with high quality and optimized settings
plt.savefig(
    output,
    format="svg",
    dpi=300,
    bbox_inches="tight",
    facecolor="white",
    edgecolor="none",
    metadata={
        "Creator": f"uutils {args.project} tracking",
        "Title": f"{title} Test Suite Results",
    },
)
