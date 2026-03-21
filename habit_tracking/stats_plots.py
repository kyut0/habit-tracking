"""
habit_tracking/stats_plots.py

Matplotlib figures for the Comparison and Statistical Analysis Streamlit tabs.

All public functions accept plain DataFrames / dicts (no tracker/model objects)
and return a matplotlib Figure. They do NOT call plt.show().

Style mirrors HabitPlotter._apply_style from plots.py (grey background,
white grid, no spines) for a consistent look across the app.
"""
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from habit_tracking import config

PALETTE = sns.color_palette('muted')
SEASON_COLORS = {
    'Spring': '#2ecc71',
    'Summer': '#f39c12',
    'Fall':   '#e67e22',
    'Winter': '#3498db',
}
SEASON_ORDER = ['Spring', 'Summer', 'Fall', 'Winter']


# ── Shared style helper ────────────────────────────────────────────────────────

def _apply_style(ax, title=None, xlabel=None, ylabel=None, rotate_x=True):
    """Mirror HabitPlotter._apply_style for visual consistency."""
    ax.set_facecolor('#EBEBEB')
    ax.figure.patch.set_facecolor('white')
    ax.grid(True, color='white', linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    if title:
        ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=11)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11)
    if rotate_x:
        ax.tick_params(axis='x', rotation=45, labelsize=10)
    ax.tick_params(axis='y', labelsize=10)


# ── Comparison Tab ─────────────────────────────────────────────────────────────

def plot_yoy_mental_health(df_int: pd.DataFrame) -> plt.Figure:
    """
    Year-over-year Mental Health comparison: one subplot per calendar year.
    Each panel shows daily scatter + 30-day rolling average + annual mean line.
    """
    years = sorted(df_int['Year'].unique())
    n = len(years)
    palette = plt.cm.tab10(np.linspace(0, 1, max(n, 2)))

    fig, axes = plt.subplots(1, n, figsize=(max(4 * n, 8), 4), sharey=True)
    if n == 1:
        axes = [axes]

    for ax, year, color in zip(axes, years, palette):
        yr = (df_int[df_int['Year'] == year][['Date', 'Mental_Health']]
              .dropna().sort_values('Date'))
        yr['DayOfYear'] = yr['Date'].dt.dayofyear

        ax.scatter(yr['DayOfYear'], yr['Mental_Health'],
                   alpha=0.25, color=color, s=8)
        roll = (yr.set_index('DayOfYear')['Mental_Health']
                .rolling(30, min_periods=5).mean())
        ax.plot(roll.index, roll.values, color=color, linewidth=2)

        mean_val = yr['Mental_Health'].mean()
        ax.axhline(mean_val, linestyle='--', color='grey', linewidth=1,
                   label=f'μ = {mean_val:.1f}')
        _apply_style(ax, title=str(year), xlabel='Day of year', rotate_x=False)
        ax.set_ylim(0, 11)
        ax.legend(fontsize=8, loc='lower right')

    axes[0].set_ylabel('Mental Health Score (1–10)')
    fig.suptitle('Mental Health — Year over Year', fontsize=14, fontweight='bold', y=1.02)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def plot_annual_mh_trend(df_int: pd.DataFrame) -> plt.Figure:
    """
    Annual mean Mental Health with 95% confidence intervals.
    Used as a summary companion to the per-year panels.
    """
    annual = df_int.groupby('Year')['Mental_Health'].agg(['mean', 'std', 'count'])
    annual['se'] = annual['std'] / np.sqrt(annual['count'])

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.errorbar(annual.index, annual['mean'],
                yerr=annual['se'] * 1.96,
                fmt='o-', color=PALETTE[0], capsize=5,
                linewidth=2, markersize=7, zorder=3)

    for year, row in annual.iterrows():
        ax.text(year, row['mean'] + annual['se'].max() * 2.5 + 0.1,
                f"{row['mean']:.2f}", ha='center', fontsize=9)

    _apply_style(ax, title='Annual Mean Mental Health (±95% CI)',
                 xlabel='Year', ylabel='Mean Score', rotate_x=False)
    ax.set_ylim(0, 11)
    ax.set_xticks(annual.index)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def plot_yoy_habits(df_int: pd.DataFrame, habit_cols: list) -> plt.Figure:
    """
    Annual habit completion rates (% of tracked days) as a multi-line chart.
    Shows a curated set of habits; colours from config.VAR_COLORS.
    """
    highlight = [h for h in ['Exercised', 'Danced', 'Mindfulness', 'Cold_Plunge',
                              'Alcohol', 'Weed', 'Made_Bed', 'Morning_Pages']
                 if h in habit_cols]
    yoy = df_int.groupby('Year')[highlight].mean() * 100

    fig, ax = plt.subplots(figsize=(10, 5))
    for habit in highlight:
        color = config.VAR_COLORS.get(habit, '#888888')
        ax.plot(yoy.index, yoy[habit], marker='o', label=habit,
                color=color, linewidth=2, markersize=6)

    _apply_style(ax, title='Habit Completion Rates — Year over Year',
                 xlabel='Year', ylabel='% of tracked days', rotate_x=False)
    ax.set_xticks(yoy.index)
    ax.set_ylim(0, 105)
    ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0),
              fontsize=9, frameon=False)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def plot_seasonal_mh(df_int: pd.DataFrame) -> plt.Figure:
    """
    Mental Health by season: bar chart (with 95% CI) + box plot side by side.
    Kruskal-Wallis p-value annotated on the box plot.
    """
    seasonal = df_int.groupby('Season')['Mental_Health'].agg(['mean', 'std', 'count'])
    seasonal = seasonal.reindex(SEASON_ORDER).dropna()
    seasonal['se'] = seasonal['std'] / np.sqrt(seasonal['count'])

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Bar chart
    bars = axes[0].bar(
        seasonal.index, seasonal['mean'],
        yerr=seasonal['se'] * 1.96, capsize=5,
        color=[SEASON_COLORS[s] for s in seasonal.index], edgecolor='none'
    )
    for bar, (_, row) in zip(bars, seasonal.iterrows()):
        axes[0].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.15,
                     f'{row["mean"]:.2f}', ha='center', fontsize=9, fontweight='bold')
    _apply_style(axes[0], title='Mean Mental Health by Season (±95% CI)',
                 ylabel='Mean Score', rotate_x=False)
    axes[0].set_ylim(0, 11)

    # Box plot
    groups = [df_int.loc[df_int['Season'] == s, 'Mental_Health'].dropna()
              for s in SEASON_ORDER if s in df_int['Season'].values]
    valid_seasons = [s for s in SEASON_ORDER if s in df_int['Season'].values]
    bp = axes[1].boxplot(groups, labels=valid_seasons, patch_artist=True,
                         medianprops=dict(color='black', linewidth=2))
    for patch, season in zip(bp['boxes'], valid_seasons):
        patch.set_facecolor(SEASON_COLORS[season])

    kw_stat, kw_p = __import__('scipy').stats.kruskal(*groups)
    axes[1].text(0.98, 0.03, f'Kruskal-Wallis p={kw_p:.4f}',
                 transform=axes[1].transAxes, ha='right', fontsize=9, color='grey')
    _apply_style(axes[1], title='Mental Health Distribution by Season',
                 ylabel='Score', rotate_x=False)
    axes[1].set_ylim(0, 11)

    fig.suptitle('Seasonal Mental Health Patterns', fontsize=14, fontweight='bold')
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def plot_seasonal_habits(df_int: pd.DataFrame, habit_cols: list) -> plt.Figure:
    """
    Habit completion rates (%) by season — one subplot per habit.
    """
    habits = [h for h in ['Exercised', 'Cold_Plunge', 'Danced', 'Mindfulness',
                           'Morning_Pages', 'Alcohol', 'Weed', 'Made_Bed']
              if h in habit_cols]
    seasonal = df_int.groupby('Season')[habits].mean() * 100
    seasonal = seasonal.reindex([s for s in SEASON_ORDER if s in seasonal.index])

    n = len(habits)
    ncols = 4
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 4 * nrows))
    flat = axes.flatten() if n > 1 else [axes]

    for ax, habit in zip(flat, habits):
        vals = seasonal[habit].dropna()
        ax.bar(vals.index, vals.values,
               color=[SEASON_COLORS[s] for s in vals.index], edgecolor='none')
        _apply_style(ax, title=habit, ylabel='% days', rotate_x=False)
        ax.set_xticklabels(vals.index, rotation=30, ha='right', fontsize=8)
        ax.set_ylim(0, max(vals.max() * 1.3 + 2, 5))

    for ax in flat[n:]:
        ax.set_visible(False)

    fig.suptitle('Habit Completion by Season', fontsize=14, fontweight='bold')
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def plot_monthly_habit_heatmap(df_int: pd.DataFrame, habit_cols: list) -> plt.Figure:
    """
    Heatmap: rows = habits (sorted by overall frequency), columns = month of year.
    Values are % of tracked days. Aggregated across all years.
    """
    monthly = df_int.groupby('Month')[habit_cols].mean() * 100
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly.index = [labels[m - 1] for m in monthly.index]
    habit_order = monthly.mean().sort_values(ascending=False).index.tolist()
    monthly = monthly[habit_order]

    fig, ax = plt.subplots(figsize=(14, max(6, len(habit_order) * 0.5 + 2)))
    sns.heatmap(
        monthly.T, ax=ax,
        cmap='YlGnBu', vmin=0, vmax=100,
        annot=True, fmt='.0f', annot_kws={'size': 8},
        linewidths=0.5, linecolor='white',
        cbar_kws={'label': '% of tracked days', 'shrink': 0.7},
    )
    ax.set_title('Habit Completion Rate by Month of Year\n'
                 '(% of tracked days, aggregated across all years)',
                 fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('')
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


# ── Analysis Tab ───────────────────────────────────────────────────────────────

def plot_correlation_forest(results_df: pd.DataFrame) -> plt.Figure:
    """
    Forest plot: Δ Mental Health (habit done − not done) for each habit.
    Green bars = positive effect, red = negative.
    ★ marks habits significant after BH correction.
    """
    sorted_df = results_df.sort_values('MH_diff')
    colors = ['#2ecc71' if d > 0 else '#e74c3c' for d in sorted_df['MH_diff']]

    fig, ax = plt.subplots(figsize=(9, max(5, len(sorted_df) * 0.45)))
    ax.barh(sorted_df['Habit'], sorted_df['MH_diff'],
            color=colors, edgecolor='none')
    ax.axvline(0, color='black', linewidth=1)

    for _, row in sorted_df.iterrows():
        if row.get('sig_BH', False):
            y_pos = list(sorted_df['Habit']).index(row['Habit'])
            offset = 0.02 if row['MH_diff'] > 0 else -0.02
            ha = 'left' if row['MH_diff'] > 0 else 'right'
            ax.text(row['MH_diff'] + offset, y_pos, '★',
                    va='center', ha=ha, fontsize=13, color='black')

    _apply_style(ax,
                 title='Effect of Each Habit on Mental Health\n★ = significant (BH-corrected, α=0.05)',
                 xlabel='Δ Mean Mental Health Score (habit done − not done)',
                 rotate_x=False)
    ax.text(0.98, 0.01, 'Green = positive  |  Red = negative',
            transform=ax.transAxes, ha='right', fontsize=9, color='grey')
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def plot_habit_mh_boxplot(df_int: pd.DataFrame, habit: str) -> plt.Figure:
    """
    Single habit: box plots of Mental_Health for done vs not-done days.
    Used in the interactive habit explorer.
    """
    sub = df_int[['Date', habit, 'Mental_Health']].dropna()
    done = sub.loc[sub[habit] == 1, 'Mental_Health']
    not_done = sub.loc[sub[habit] == 0, 'Mental_Health']

    fig, ax = plt.subplots(figsize=(5, 4))
    bp = ax.boxplot([not_done, done],
                    labels=[f'No {habit}', habit],
                    patch_artist=True,
                    medianprops=dict(color='black', linewidth=2))
    bp['boxes'][0].set_facecolor('#f0f0f0')
    bp['boxes'][1].set_facecolor(config.VAR_COLORS.get(habit, PALETTE[0]))

    _, p_mw = __import__('scipy').stats.mannwhitneyu(done, not_done, alternative='two-sided')
    diff = done.mean() - not_done.mean()
    ax.set_title(f'{habit}: Δ = {diff:+.2f}  (MW p = {p_mw:.4f})',
                 fontsize=11, fontweight='bold')
    _apply_style(ax, ylabel='Mental Health Score', rotate_x=False)
    ax.set_ylim(0.5, 10.5)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def plot_regression_coefficients(coef_df: pd.DataFrame, r_squared: float,
                                  mh_lag_coef: float, mh_lag_p: float) -> plt.Figure:
    """
    Coefficient plot for habit predictors in the OLS model.
    MH_lag1 (the autocorrelation control variable) is excluded from bars
    and annotated as a footnote instead.
    Error bars = 95% confidence intervals (HAC).
    """
    colors = ['#e74c3c' if c < 0 else '#2ecc71' for c in coef_df['Coef']]

    fig, ax = plt.subplots(figsize=(9, max(5, len(coef_df) * 0.45)))
    ax.barh(coef_df['Habit'], coef_df['Coef'],
            xerr=[coef_df['Coef'] - coef_df['CI_low'],
                  coef_df['CI_high'] - coef_df['Coef']],
            color=colors, capsize=4, edgecolor='none')
    ax.axvline(0, color='black', linewidth=1)

    for _, row in coef_df.iterrows():
        if row.get('sig', False):
            y_pos = list(coef_df['Habit']).index(row['Habit'])
            ax.text(row['CI_high'] + 0.01, y_pos, '★', va='center', fontsize=11)

    ax.text(0.98, 0.02,
            f'Mood autocorrelation (MH_lag1): β = {mh_lag_coef:.3f},  p = {mh_lag_p:.4f}',
            transform=ax.transAxes, ha='right', fontsize=9,
            color='#555555', style='italic')

    _apply_style(ax,
                 title=f'OLS Coefficients — Controlling for Yesterday\'s Mood\n'
                       f'R² = {r_squared:.3f}  |  HAC standard errors  |  ★ p < 0.05',
                 xlabel='Effect on Mental Health score (holding other habits constant)',
                 rotate_x=False)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def plot_endogeneity(endo_results: list, df_int: pd.DataFrame) -> plt.Figure | None:
    """
    Boxplots of yesterday's Mental_Health stratified by today's substance use.
    Shows whether prior mood predicts next-day use (reverse causality).
    Returns None if no substances have sufficient data.
    """
    sufficient = [r for r in endo_results if r.get('sufficient_data')]
    if not sufficient:
        return None

    substances = [r['substance'] for r in sufficient]
    endo = df_int.sort_values('Date').copy()
    endo['MH_lag1'] = endo['Mental_Health'].shift(1)
    gap = (endo['Date'] - endo['Date'].shift(1)).dt.days
    endo.loc[gap != 1, 'MH_lag1'] = np.nan
    endo = endo.dropna(subset=['MH_lag1'])

    fig, axes = plt.subplots(1, len(substances),
                             figsize=(5 * len(substances), 4))
    if len(substances) == 1:
        axes = [axes]

    for ax, r in zip(axes, sufficient):
        substance = r['substance']
        sub = endo.dropna(subset=[substance, 'MH_lag1'])
        groups = [sub.loc[sub[substance] == 0, 'MH_lag1'],
                  sub.loc[sub[substance] == 1, 'MH_lag1']]
        bp = ax.boxplot(groups,
                        labels=[f'No {substance}\ntoday', f'{substance}\ntoday'],
                        patch_artist=True,
                        medianprops=dict(color='black', linewidth=2))
        bp['boxes'][0].set_facecolor('#f0f0f0')
        bp['boxes'][1].set_facecolor(config.VAR_COLORS.get(substance, PALETTE[1]))

        sig_marker = '★' if r['significant'] else ''
        ax.set_title(f"MH yesterday by {substance} use today {sig_marker}",
                     fontsize=10, fontweight='bold')
        _apply_style(ax, ylabel="Yesterday's Mental Health", rotate_x=False)
        ax.set_ylim(0.5, 10.5)

    fig.suptitle('Reverse Causality: Does Prior Mood Predict Substance Use?',
                 fontsize=12, fontweight='bold')
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def plot_stationarity_visual(df_int: pd.DataFrame) -> plt.Figure:
    """
    Rolling mean and rolling std of Mental_Health over time.
    A flat rolling mean + flat rolling std = consistent with stationarity.
    """
    series = (df_int[['Date', 'Mental_Health']]
              .dropna().sort_values('Date')
              .set_index('Date')['Mental_Health'])

    fig, axes = plt.subplots(2, 1, figsize=(12, 5), sharex=True)
    roll_mean = series.rolling(60).mean()
    roll_std = series.rolling(60).std()

    axes[0].plot(series, alpha=0.2, color=PALETTE[0], linewidth=0.8)
    axes[0].plot(roll_mean, color=PALETTE[0], linewidth=2,
                 label='60-day rolling mean')
    axes[0].legend(fontsize=9)
    _apply_style(axes[0], ylabel='Mental Health', rotate_x=False)

    axes[1].plot(roll_std, color=PALETTE[1], linewidth=2,
                 label='60-day rolling std dev')
    axes[1].legend(fontsize=9)
    _apply_style(axes[1], xlabel='Date', ylabel='Std Dev', rotate_x=False)

    fig.suptitle('Stationarity Visual Check (flat lines → stationary)',
                 fontsize=13, fontweight='bold')
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig
