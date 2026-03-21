from pathlib import Path

from habit_tracking import config

# Load packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.cm as cm
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

sns.set_palette("deep")

class HabitPlotter:
    @property
    def boolean_variables(self):
        """Returns BOOLEAN_VARIABLES filtered to columns present in self.df (e.g. after combining Delta8/Weed)"""
        return [var for var in config.BOOLEAN_VARIABLES if var in self.df.columns]

    # ── Shared style helpers ────────────────────────────────────────────────────

    def _apply_style(self, ax, title=None, xlabel=None, ylabel=None):
        """Apply uniform style to an axes: grey background, white grid, no spines."""
        ax.set_facecolor('#EBEBEB')
        ax.figure.patch.set_facecolor('white')
        ax.grid(True, color='white', linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=11)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=11)
        ax.tick_params(axis='x', rotation=90, labelsize=10)
        ax.tick_params(axis='y', labelsize=10)

    def _make_legend_fig(self, handles, labels, title=None):
        """Return a standalone figure containing only the legend."""
        n = len(labels)
        fig_legend = plt.figure(figsize=(2.5, max(1.0, n * 0.35 + 0.5)))
        fig_legend.legend(handles, labels, loc='center', title=title,
                          frameon=False, fontsize=10)
        fig_legend.patch.set_facecolor('white')
        return fig_legend

    # ── Data prep ───────────────────────────────────────────────────────────────

    def plot_prep(self, start_date=None, end_date=None):
        """Run all necessary data preparation steps for plotting"""
        self.convert_df_to_long()
        self.filter_dates(start_date=start_date, end_date=end_date)
        self.aggregate_monthly_stats()

    def plot_all(self):
        """Generate all plots"""
        self.plot_prep()
        self.plot_total_barchart()
        self.plot_mental_health_trend()
        self.plot_monthly_percentages()

    def convert_df_to_long(self):
        """Convert self.df to long format for easier plotting"""
        if self.df is None:
            return None

        self.df_long = pd.melt(self.df, id_vars=['Date'], value_vars=self.boolean_variables,
                               var_name='Habit', value_name='Value')

        self.df_long['Year'] = pd.to_datetime(self.df_long['Date']).dt.year
        self.df_long['Month'] = pd.to_datetime(self.df_long['Date']).dt.month

        self.df_long['Year_Month'] = self.df_long.apply(
            lambda x: f"{int(x['Year'])}-{int(x['Month']):02d}", axis=1
        )

    def filter_dates(self, start_date=None, end_date=None):
        """Filter self.df_long and self.df to only include data within the provided date range"""
        if self.df_long is None:
            return None
        if self.df is None:
            return None

        if start_date:
            start_ts = pd.Timestamp(start_date)
            self.df_long = self.df_long[pd.to_datetime(self.df_long['Date']) >= start_ts]
            self.df = self.df[pd.to_datetime(self.df['Date']) >= start_ts]
        if end_date:
            end_ts = pd.Timestamp(end_date)
            self.df_long = self.df_long[pd.to_datetime(self.df_long['Date']) <= end_ts]
            self.df = self.df[pd.to_datetime(self.df['Date']) <= end_ts]

    def aggregate_monthly_stats(self):
        """Aggregate daily data to monthly statistics (percentages & counts)"""
        if self.df_long is None:
            return None

        self.df_monthly_perc = self.df_long.groupby(['Year_Month', 'Habit'])['Value'].mean().reset_index()
        self.df_monthly_perc['Percentage'] = self.df_monthly_perc['Value'] * 100
        self.df_monthly_perc = self.df_monthly_perc.drop(columns=['Value'])

        self.df_monthly_raw = self.df_long.groupby(['Year_Month', 'Habit'])['Value'].sum().reset_index()
        self.df_monthly_raw = self.df_monthly_raw.rename(columns={'Value': 'Count'})

    # ── Plot methods ────────────────────────────────────────────────────────────

    def plot_cumulative_habits(self):
        """Plot cumulative habits over time. Returns (fig, legend_fig)."""
        fig, ax = plt.subplots(figsize=(15, 8))
        handles, labels = [], []

        for var in self.boolean_variables:
            var_data = self.df[['Date', var]].dropna(subset=[var])
            cumsum = var_data[var].cumsum()
            line, = ax.plot(var_data['Date'], cumsum,
                            color=config.VAR_COLORS.get(var, 'gray'))
            handles.append(line)
            labels.append(var)

        self._apply_style(ax, title='Cumulative Habits Over Time',
                          xlabel='Date', ylabel='Number of Days')

        return fig, self._make_legend_fig(handles, labels)

    def plot_monthly_percentages(self, selected_habits=None):
        """Plot monthly percentages of habits over time. Returns (fig, legend_fig)."""
        df_long = self.df_monthly_perc.copy()

        if selected_habits:
            df_long = df_long[df_long['Habit'].isin(selected_habits)]

        fig, ax = plt.subplots(figsize=(15, 8))
        handles, labels = [], []

        for var in self.boolean_variables:
            if selected_habits and var not in selected_habits:
                continue
            var_data = df_long[df_long['Habit'] == var]
            line, = ax.plot(var_data['Year_Month'], var_data['Percentage'],
                            color=config.VAR_COLORS.get(var, 'gray'))
            handles.append(line)
            labels.append(var)

        self._apply_style(ax, title='Monthly Percentages of Habits',
                          xlabel='Month', ylabel='Percentage (%)')

        return fig, self._make_legend_fig(handles, labels)

    def plot_total_barchart(self):
        """Plot total counts of habits as a bar chart. Returns (fig, None)."""
        df_long = self.df_long.copy()
        total_counts = df_long.groupby('Habit')['Value'].sum().reset_index()
        total_counts = total_counts.sort_values(by='Value', ascending=False)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(total_counts['Habit'], total_counts['Value'],
               color=total_counts['Habit'].map(config.VAR_COLORS).fillna('gray'))

        self._apply_style(ax, title='Total Counts of Habits',
                          xlabel='Habit', ylabel='Total Count')

        return fig, None

    def plot_monthly_summary(self, year_month=None):
        """Plot a summary of monthly statistics for a single year-month. Returns (fig, None)."""
        df_long = self.df_monthly_perc.copy()
        if year_month:
            df_long = df_long[df_long['Year_Month'] == year_month]
        df_long = df_long.sort_values(by='Percentage', ascending=False)

        fig, ax = plt.subplots(figsize=(15, 10))
        ax.bar(df_long['Habit'], df_long['Percentage'],
               color=df_long['Habit'].map(config.VAR_COLORS).fillna('gray'))

        title = f'Monthly Summary of Habits — {year_month}' if year_month else 'Monthly Summary of Habits'
        self._apply_style(ax, title=title, xlabel='Habit', ylabel='Percentage (%)')

        return fig, None

    def plot_mental_health_trend(self):
        """Plot mental health trend over time. Returns (fig, None)."""
        fig, ax = plt.subplots(figsize=(15, 6))

        mental_health = self.df[['Date', 'Mental_Health']].copy()

        ax.plot(mental_health['Date'], mental_health['Mental_Health'],
                color='grey', alpha=0.5)

        window_size = 30
        rolling_mean = mental_health['Mental_Health'].rolling(window=window_size, center=True, min_periods=1).mean()
        ax.plot(mental_health['Date'], rolling_mean, color='black', linewidth=2)

        self._apply_style(ax, title='Mental Health Over Time',
                          xlabel='Date', ylabel='Mental Health Score (1-10)')

        return fig, None

    def plot_monthly_heatmap(self):
        """Plot a heatmap of monthly statistics. Returns (fig, None)."""
        heatmap_data = self.df_monthly_perc.copy()
        pivot_table = heatmap_data.pivot(
            index='Year_Month', columns='Habit', values='Percentage'
        )
        pivot_table = pivot_table.astype(float).fillna(0)
        col_order = config.GOAL_COLS.keys()
        pivot_table = pivot_table.reindex(columns=[c for c in col_order if c in pivot_table.columns])
        
        fig = plt.figure(figsize=(15, 11))
        gs = fig.add_gridspec(2, 1, height_ratios=[10, 0.4], hspace=0.05)
        ax = fig.add_subplot(gs[0])
        cbar_ax = fig.add_subplot(gs[1])

        sns.heatmap(pivot_table, cmap='magma_r',
                    cbar_ax=cbar_ax, cbar_kws={'label': 'Percentage (%)', 'orientation': 'horizontal'},
                    xticklabels=True, yticklabels=True, square=True, ax=ax)

        self._apply_style(ax, title='Monthly Percentages Heatmap')
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        ax.invert_yaxis()

        fig.tight_layout()
        hm_pos = ax.get_position()
        cb_pos = cbar_ax.get_position()
        cbar_ax.set_position([hm_pos.x0, cb_pos.y0, hm_pos.width, cb_pos.height])

        return fig, None
    
    def plot_monthly_goal_achievement(self):
        """Plot a heatmap of monthly goal achievement. Returns (fig, None)."""
        heatmap_data = self.df_monthly_perc.copy()
        pivot_table = heatmap_data.pivot(
            index='Year_Month', columns='Habit', values='Percentage'
        )
        pivot_table = pivot_table.astype(float).fillna(0)
        col_order = config.GOAL_COLS.keys()
        pivot_table = pivot_table.reindex(columns=[c for c in col_order if c in pivot_table.columns])
        
        for col in pivot_table.columns:
            if col in config.POS_GOALS:
                pivot_table[col] = pivot_table[col] >= config.GOAL_COLS[col]
            elif col in config.NEG_GOALS:
                pivot_table[col] = pivot_table[col] < config.GOAL_COLS[col]
        
        pivot_table = pivot_table.astype(float)
        
        fig = plt.figure(figsize=(15, 11))
        gs = fig.add_gridspec(2, 1, height_ratios=[10, 0.4], hspace=0.05)
        ax = fig.add_subplot(gs[0])
        legend_ax = fig.add_subplot(gs[1])

        sns.heatmap(pivot_table, cmap=LinearSegmentedColormap.from_list('goal', ['white', 'limegreen']),
                    vmin=0, vmax=1, cbar=False,
                    xticklabels=True, yticklabels=True, square=True, ax=ax)

        self._apply_style(ax, title='Monthly Goal Achievement')
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        ax.invert_yaxis()

        from matplotlib.patches import Patch
        legend_ax.legend(
            handles=[Patch(facecolor='white', edgecolor='gray', label='Not achieved'),
                     Patch(facecolor='limegreen', label='Achieved')],
            loc='center', ncol=2, frameon=False, fontsize=10
        )
        legend_ax.axis('off')

        fig.tight_layout()
        hm_pos = ax.get_position()
        lg_pos = legend_ax.get_position()
        legend_ax.set_position([hm_pos.x0, lg_pos.y0, hm_pos.width, lg_pos.height])

        return fig, None

    def plot_medications(self):
        """Plot medication usage over time. Returns (fig, legend_fig)."""
        if self.meds_data is None:
            return None, None

        meds_data = self.meds_data.copy()
        unique_meds = meds_data['Medication_Generic'].unique()
        colors = cm.get_cmap('tab10', len(unique_meds))
        color_map = {med: colors(i) for i, med in enumerate(unique_meds)}
        med_colors = meds_data['Medication_Generic'].map(color_map)

        fig, ax = plt.subplots(figsize=(15, 10))
        ax.hlines(
            y=meds_data['Dose (mg)'],
            xmin=meds_data['Start_Date'],
            xmax=meds_data['End_Date'],
            colors=med_colors,
            alpha=0.6,
            linewidth=3
        )

        self._apply_style(ax, title='Medication Usage Over Time',
                          xlabel='Date', ylabel='Dose (mg)')

        handles = [Line2D([0], [0], color=color_map[med], lw=4) for med in unique_meds]
        labels = list(unique_meds)

        return fig, self._make_legend_fig(handles, labels, title='Medication')

    def plot_sleep_pattern(self):
        """Plot sleep patterns over time. Returns (fig, None)."""
        sleep_time = self.sleep_data
        if sleep_time is None:
            return None, None

        fig, ax = plt.subplots(figsize=(15, 10))
        ax.hlines(
            y=sleep_time['Date'],
            xmin=sleep_time['Start_Hour'],
            xmax=sleep_time['End_Hour'],
            color='navy',
            alpha=0.3,
            linewidth=1
        )

        ax.set_xlim(20, 32)
        xticks = list(range(20, 33, 2))
        ax.set_xticks(xticks)
        ax.set_xticklabels([f"{h % 24:02d}:00" for h in xticks])

        self._apply_style(ax, title='Sleep Patterns Over Time',
                          xlabel='Time of Day (Hours)', ylabel='Date')

        return fig, None

    def plot_sleep_quality(self):
        """Plot average monthly sleep quality over time. Returns (fig, None)."""
        if self.sleep_data is None:
            return None, None

        self.sleep_data['Sleep_Quality_Num'] = self.sleep_data['Sleep_Quality'].str.rstrip('%').astype(float)
        self.sleep_data['Year_Month'] = pd.to_datetime(self.sleep_data['Sleep_End']).dt.strftime('%Y-%m')
        monthly_quality = self.sleep_data.groupby('Year_Month')['Sleep_Quality_Num'].mean().reset_index()
        monthly_quality['Date'] = pd.to_datetime(monthly_quality['Year_Month'] + '-01')

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(monthly_quality['Date'], monthly_quality['Sleep_Quality_Num'],
                marker='o', linestyle='-', color='navy')

        self._apply_style(ax, title='Average Monthly Sleep Quality',
                          xlabel='Month', ylabel='Sleep Quality (%)')

        return fig, None

    def plot_weight_trends(self):
        """Plot weight trends over time with a smoothed line. Returns (fig, None)."""
        if self.weight_data is None:
            return None, None

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.scatter(self.weight_data['Date'], self.weight_data['Weight_lb'],
                   color='grey', alpha=0.5, s=20)

        x = np.array([(d - self.weight_data['Date'].min()).days for d in self.weight_data['Date']])
        y = self.weight_data['Weight_lb'].values
        z = np.polyfit(x, y, 5)
        p = np.poly1d(z)
        x_smooth = np.linspace(x.min(), x.max(), 300)
        y_smooth = p(x_smooth)
        dates_smooth = [self.weight_data['Date'].min() + timedelta(days=int(d)) for d in x_smooth]
        ax.plot(dates_smooth, y_smooth, color='navy')

        self._apply_style(ax, title='Weight Trends Over Time',
                          xlabel='Date', ylabel='Weight (lb)')

        return fig, None

    def plot_goal_heatmap(self, start_date=None):
        """Plot a heatmap showing goal achievement. Returns (fig, None)."""
        monthly_stats = self.df_monthly_perc.copy()

        if start_date:
            monthly_stats = monthly_stats[monthly_stats['Year_Month'] >= start_date]

        for var, goal in self.positive_goals.items():
            if var in monthly_stats.columns:
                monthly_stats[f'{var}_Achieved'] = monthly_stats[var] > goal

        for var, goal in self.negative_goals.items():
            if var in monthly_stats.columns:
                monthly_stats[f'{var}_Achieved'] = monthly_stats[var] < goal

        achieved_cols = [col for col in monthly_stats.columns if col.endswith('_Achieved')]
        heatmap_data = monthly_stats.melt(
            id_vars=['Year_Month'], value_vars=achieved_cols,
            var_name='Variable', value_name='Achieved'
        )
        heatmap_data['Variable'] = heatmap_data['Variable'].str.replace('_Achieved', '')

        pivot_table = heatmap_data.pivot(
            index='Year_Month', columns='Variable', values='Achieved'
        )

        fig, ax = plt.subplots(figsize=(15, 10))
        sns.heatmap(pivot_table, cmap=['white', 'green'], cbar=False,
                    xticklabels=True, yticklabels=True, ax=ax)

        self._apply_style(ax, title='Monthly Goal Achievement')

        return fig, None
