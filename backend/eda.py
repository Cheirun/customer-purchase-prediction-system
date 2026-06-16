# eda.py
# -------------------------------------------------
# exploratory data analysis
# always do this before training anything
# found out income and mins_on_site are the most correlated
# with the target - makes sense intuitively
# -------------------------------------------------

import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')   # headless mode for server
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams.update({'figure.dpi': 140, 'axes.titlesize': 12})

OUT = 'static/charts'   # where to save the charts


def _save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = f'{OUT}/{name}.png'
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    print(f'  [eda] saved → {name}.png')


def plot_purchase_balance(df):
    """just checking if the classes are balanced - they roughly are (~55/45)"""
    counts = df['bought_it'].value_counts().sort_index()
    labels = ["Didn't Buy", "Bought"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.suptitle('Purchase Distribution', fontweight='bold')

    ax1.bar(labels, counts, color=['#e05c5c', '#3dba8c'], edgecolor='white', width=0.45)
    ax1.set_ylabel('Count')
    for i, v in enumerate(counts):
        ax1.text(i, v + 8, str(v), ha='center', fontsize=10, fontweight='bold')

    ax2.pie(counts, labels=labels, autopct='%1.1f%%',
            colors=['#e05c5c', '#3dba8c'], startangle=140)

    _save(fig, '01_purchase_balance')


def plot_numeric_distributions(df):
    """checking for skew in numerical columns"""
    cols   = ['age', 'annual_income', 'mins_on_site', 'pages_viewed', 'prev_purchases']
    colors = ['#5b8dee', '#a855f7', '#f97316', '#22c55e', '#ec4899']

    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    axes = axes.flatten()
    fig.suptitle('Feature Distributions', fontweight='bold')

    for i, col in enumerate(cols):
        axes[i].hist(df[col].dropna(), bins=22, color=colors[i],
                     edgecolor='white', alpha=0.85, rwidth=0.88)
        axes[i].set_title(col.replace('_', ' ').title())
        axes[i].set_xlabel('Value')
        axes[i].set_ylabel('Freq')

    axes[-1].axis('off')
    fig.tight_layout()
    _save(fig, '02_numeric_distributions')


def plot_correlation_heatmap(df):
    """income is most correlated with buying - good sign for the model"""
    num_cols = ['age', 'annual_income', 'mins_on_site', 'pages_viewed',
                'prev_purchases', 'discount_given', 'bought_it']
    corr = df[num_cols].corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
                square=True, linewidths=0.4, ax=ax, cbar_kws={'shrink': 0.8})
    ax.set_title('Correlation Matrix', fontweight='bold')
    fig.tight_layout()
    _save(fig, '03_correlation_heatmap')


def plot_categorical_purchase_rates(df):
    """wanted to see if device type has any effect - mobile slightly lower"""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    fig.suptitle('Purchase Rate by Category', fontweight='bold')

    cats = ['gender', 'device_used', 'discount_given']
    for ax, col in zip(axes, cats):
        rates = df.groupby(col)['bought_it'].mean().sort_values()
        bars  = ax.barh(rates.index.astype(str), rates.values,
                        color='#5b8dee', edgecolor='white')
        ax.set_xlim(0, 1.05)
        ax.set_xlabel('Purchase Rate')
        ax.set_title(col.replace('_', ' ').title())
        for bar, val in zip(bars, rates.values):
            ax.text(val + 0.01, bar.get_y() + bar.get_height() / 2,
                    f'{val:.0%}', va='center', fontsize=9)

    fig.tight_layout()
    _save(fig, '04_categorical_rates')


def plot_income_vs_purchase(df):
    """boxplot shows clear income difference between buyers and non-buyers"""
    fig, ax = plt.subplots(figsize=(7, 4))
    df_plot = df[['annual_income', 'bought_it']].dropna()
    df_plot['Group'] = df_plot['bought_it'].map({0: "Didn't Buy", 1: 'Bought'})

    sns.boxplot(data=df_plot, x='Group', y='annual_income',
                palette=['#e05c5c', '#3dba8c'], ax=ax, width=0.45)
    ax.set_title('Income vs Purchase Decision', fontweight='bold')
    ax.set_ylabel('Annual Income (₹)')
    ax.set_xlabel('')
    fig.tight_layout()
    _save(fig, '05_income_vs_purchase')


def run_full_eda(df):
    print('[eda] running analysis...')
    plot_purchase_balance(df)
    plot_numeric_distributions(df)
    plot_correlation_heatmap(df)
    plot_categorical_purchase_rates(df)
    plot_income_vs_purchase(df)
    print('[eda] done.\n')


if __name__ == '__main__':
    from data_loader import load_data
    df = load_data()
    run_full_eda(df)
