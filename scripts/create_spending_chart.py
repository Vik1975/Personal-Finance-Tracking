#!/usr/bin/env python3
"""Generate a bar chart showing spending by category for December 2025."""

import json

import matplotlib.pyplot as plt

# Read analytics data
with open("/tmp/analytics.json", "r") as f:
    data = json.load(f)

# Filter out uncategorized and extract categorized data
categorized = [item for item in data if item["category_id"] is not None]

# Sort by total amount descending
categorized.sort(key=lambda x: float(x["total"]), reverse=True)

# Extract data for chart
categories = [item["category_name"] for item in categorized]
amounts = [float(item["total"]) for item in categorized]
colors = ["#4CAF50", "#2196F3", "#FFC107", "#FF5722", "#9C27B0"]

# Create bar chart
fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.bar(
    categories, amounts, color=colors[: len(categories)], edgecolor="black", linewidth=1.5
)

# Customize chart
ax.set_xlabel("Category", fontsize=14, fontweight="bold")
ax.set_ylabel("Spending ($)", fontsize=14, fontweight="bold")
ax.set_title("December 2025 Spending by Category", fontsize=16, fontweight="bold", pad=20)
ax.grid(axis="y", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Add value labels on bars
for bar, amount in zip(bars, amounts, strict=False):
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2.0,
        height,
        f"${amount:.2f}",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
    )

# Rotate x-axis labels for better readability
plt.xticks(rotation=15, ha="right", fontsize=11)
plt.yticks(fontsize=11)

# Add total spending text
total_categorized = sum(amounts)
plt.figtext(
    0.99,
    0.01,
    f"Total Spending: ${total_categorized:.2f}",
    ha="right",
    fontsize=11,
    style="italic",
    color="gray",
)

# Tight layout
plt.tight_layout()

# Save chart
output_file = "december_2025_spending_chart.png"
plt.savefig(output_file, dpi=300, bbox_inches="tight")
print(f"Chart saved to: {output_file}")

# Display summary
print("\nDecember 2025 Spending Summary:")
print("=" * 50)
for cat, amt in zip(categories, amounts, strict=False):
    print(f"{cat:20s}: ${amt:>8.2f}")
print("=" * 50)
print(f'{"Total":20s}: ${total_categorized:>8.2f}')
