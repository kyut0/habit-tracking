from pathlib import Path

from habit_tracking import config

# Load packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from datetime import timedelta
import seaborn as sns
# from wordcloud import WordCloud
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
# plt.style.use('seaborn')
sns.set_palette("deep")

class HabitPlotter:
    @property
    def boolean_variables(self):
        """Returns BOOLEAN_VARIABLES filtered to columns present in self.df (e.g. after combining Delta8/Weed)"""
        return [var for var in config.BOOLEAN_VARIABLES if var in self.df.columns]

    def plot_cumulative_habits(self):
        """Plot cumulative habits over time"""
        plt.figure(figsize=(15, 8))
        
        # Plot each variable
        for var in self.boolean_variables:
            cumsum = self.df[var].fillna(False).cumsum()
            plt.plot(self.df['Date'], cumsum, 
                    label=var, color=config.VAR_COLORS.get(var, 'gray'))
            
        plt.title('Cumulative Habits Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Days')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
    def plot_mental_health_trend(self):
        """Plot mental health trend over time"""
        plt.figure(figsize=(15, 6))
        
        # Convert Mental_Health to numeric
        mental_health_numeric = pd.to_numeric(self.df['Mental_Health'], errors='coerce')
        
        # Plot the trend
        plt.plot(self.df['Date'], mental_health_numeric, alpha=0.5)
        
        # Add smoothed trend line
        window_size = 30  # Adjust as needed
        rolling_mean = mental_health_numeric.rolling(window=window_size, center=True).mean()
        plt.plot(self.df['Date'], rolling_mean, color='red', linewidth=2)
        
        plt.title('Mental Health Over Time')
        plt.xlabel('Date')
        plt.ylabel('Mental Health Score (1-10)')
        plt.grid(True, alpha=0.3)
        
    # OTHER VERSION --------------------------------------------------------------
    def plot_monthly_heatmap(self, start_date=None):
        """Plot a heatmap of monthly statistics"""
        monthly_stats, monthly_stats_percent = self.calculate_monthly_stats()

        monthly_stats_percent.reset_index(inplace=True)

        # Create year-month column
        monthly_stats_percent['Year_Month'] = monthly_stats_percent.apply(
            lambda x: f"{int(x['Year'])}-{int(x['Month']):02d}", axis=1
        )

        # Filter by start date if provided
        if start_date:
            monthly_stats_percent = monthly_stats_percent[
                monthly_stats_percent['Year_Month'] >= start_date
            ]

        # Prepare data for heatmap
        heatmap_data = monthly_stats_percent.melt(
            id_vars=['Year_Month'],
            value_vars=self.boolean_variables + ['Mental_Health'],
            var_name='Variable',
            value_name='Percentage'
        )

        # Create heatmap
        plt.figure(figsize=(15, 10))
        pivot_table = heatmap_data.pivot(
            index='Year_Month',
            columns='Variable',
            values='Percentage'
        )

        # Replace NaN with 0
        # pivot_table.replace(np.nan, 0, inplace=True)
        pivot_table = pivot_table.astype(float).fillna(0)

        sns.heatmap(
            pivot_table,
            cmap='magma_r',
            cbar_kws={'label': 'Percentage'},
            xticklabels=True,
            yticklabels=True
        )

        plt.title('Monthly Percentages Heatmap')
        plt.xticks(rotation=90)
        plt.tight_layout()
        return plt.gcf()

    def plot_sleep_pattern(self):
        """Plot sleep patterns over time"""
        
        sleep_time = self.sleep_data
            
        if sleep_time is None:
            return None
            
        plt.figure(figsize=(15, 10))
        
        # Plot sleep segments
        plt.hlines(
            y=sleep_time['Date'],
            xmin=sleep_time['Start_Hour'],
            xmax=sleep_time['End_Hour'],
            color='navy',
            alpha=0.3,
            linewidth=1
        )
        
        plt.title('Sleep Patterns Over Time')
        plt.xlabel('Time of Day (Hours)')
        plt.ylabel('Date')
        
        # Set x-axis limits to show 24-hour period
        plt.xlim(20, 32)  # Show 8pm to 8am next day
        
        # Custom x-axis labels
        xticks = range(20, 33, 2)
        xtick_labels = [f"{h%24:02d}:00" for h in xticks]
        plt.xticks(xticks, xtick_labels)
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return plt.gcf()
        
    def plot_sleep_quality(self):
        """Plot average monthly sleep quality over time"""
        if self.sleep_data is None:
            return None
            
        # Convert sleep quality to numeric (remove % sign)
        self.sleep_data['Sleep_Quality_Num'] = self.sleep_data['Sleep_Quality'].str.rstrip('%').astype(float)
        
        # Create month column
        self.sleep_data['Year_Month'] = pd.to_datetime(self.sleep_data['Sleep_End']).dt.strftime('%Y-%m')
        
        # Calculate monthly averages
        monthly_quality = self.sleep_data.groupby('Year_Month')['Sleep_Quality_Num'].mean().reset_index()
        monthly_quality['Date'] = pd.to_datetime(monthly_quality['Year_Month'] + '-01')
        
        plt.figure(figsize=(12, 6))
        plt.plot(monthly_quality['Date'], monthly_quality['Sleep_Quality_Num'], 
                    marker='o', linestyle='-', color='navy')
        
        plt.title('Average Monthly Sleep Quality')
        plt.xlabel('Month')
        plt.ylabel('Sleep Quality (%)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return plt.gcf()
        
    def plot_weight_trends(self):
        """Plot weight trends over time with a smoothed line"""
        if self.weight_data is None:
            return None
            
        plt.figure(figsize=(12, 6))
        
        # Plot actual measurements
        plt.scatter(
            self.weight_data['Date'],
            self.weight_data['Weight_lb'],
            color='grey',
            alpha=0.5,
            s=20,
            label='Measurements'
        )
        
        # Calculate and plot trend line
        x = np.array([(d - self.weight_data['Date'].min()).days 
                        for d in self.weight_data['Date']])
        y = self.weight_data['Weight_lb'].values
        
        # Fit a polynomial
        z = np.polyfit(x, y, 5)
        p = np.poly1d(z)
        
        # Generate points for smooth curve
        x_smooth = np.linspace(x.min(), x.max(), 300)
        y_smooth = p(x_smooth)
        
        # Convert x_smooth back to dates
        dates_smooth = [self.weight_data['Date'].min() + timedelta(days=int(d)) 
                        for d in x_smooth]
        
        plt.plot(dates_smooth, y_smooth, 'navy', label='Trend')
        
        plt.title('Weight Trends Over Time')
        plt.xlabel('Date')
        plt.ylabel('Weight (lb)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        return plt.gcf()
        
    # def plot_body_composition(self):
    #     """Plot body composition trends over time"""
    #     if self.weight_data is None:
    #         return None
            
    #     # Select body composition columns
    #     composition_cols = [
    #         'Body_Fat', 'Body_Water', 'Skeletal_Muscle',
    #         'Subcutaneous_Fat', 'Visceral_Fat'
    #     ]
        
    #     # Create long format data
    #     comp_data = self.weight_data.melt(
    #         id_vars=['Date'],
    #         value_vars=composition_cols,
    #         var_name='Metric',
    #         value_name='Percentage'
    #     )
        
    #     plt.figure(figsize=(12, 6))
        
    #     # Plot each metric
    #     for metric in composition_cols:
    #         metric_data = comp_data[comp_data['Metric'] == metric]
    #         plt.plot(
    #             metric_data['Date'],
    #             metric_data['Percentage'],
    #             label=metric.replace('_', ' '),
    #             alpha=0.7,
    #             marker='o',
    #             markersize=3
    #         )
        
    #     plt.title('Body Composition Trends')
    #     plt.xlabel('Date')
    #     plt.ylabel('Percentage')
    #     plt.grid(True, alpha=0.3)
    #     plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    #     plt.tight_layout()
        
    #     return plt.gcf()
        
    def plot_goal_heatmap(self, start_date=None):
        """Plot a heatmap showing goal achievement"""
        monthly_stats = self.calculate_monthly_stats()
        
        # Create year-month column
        monthly_stats['Year_Month'] = monthly_stats.apply(
            lambda x: f"{int(x['Year'])}-{int(x['Month']):02d}", axis=1
        )
        
        # Filter by start date if provided
        if start_date:
            monthly_stats = monthly_stats[
                monthly_stats['Year_Month'] >= start_date
            ]
        
        # Process positive goals
        pos_goals_data = []
        for var, goal in self.positive_goals.items():
            if var in monthly_stats.columns:
                monthly_stats[f'{var}_Achieved'] = monthly_stats[var] > goal
                pos_goals_data.append({
                    'Variable': var,
                    'Goal': goal,
                    'Type': 'positive'
                })
                
        # Process negative goals
        neg_goals_data = []
        for var, goal in self.negative_goals.items():
            if var in monthly_stats.columns:
                monthly_stats[f'{var}_Achieved'] = monthly_stats[var] < goal
                neg_goals_data.append({
                    'Variable': var,
                    'Goal': goal,
                    'Type': 'negative'
                })
                
        # Combine goal data
        goals_data = pd.DataFrame(pos_goals_data + neg_goals_data)
        
        # Prepare data for heatmap
        achieved_cols = [col for col in monthly_stats.columns if col.endswith('_Achieved')]
        heatmap_data = monthly_stats.melt(
            id_vars=['Year_Month'],
            value_vars=achieved_cols,
            var_name='Variable',
            value_name='Achieved'
        )
        
        # Clean variable names
        heatmap_data['Variable'] = heatmap_data['Variable'].str.replace('_Achieved', '')
        
        # Create heatmap
        plt.figure(figsize=(15, 10))
        pivot_table = heatmap_data.pivot(
            index='Year_Month',
            columns='Variable',
            values='Achieved'
        )
        
        sns.heatmap(
            pivot_table,
            cmap=['white', 'green'],
            cbar=False,
            xticklabels=True,
            yticklabels=True
        )
        
        plt.title('Monthly Goal Achievement')
        plt.xticks(rotation=90)
        plt.tight_layout()
        return plt.gcf()
        
    # def plot_habit_timeline(self, start_date=None):
    #     """Plot a GitHub-style daily tracker for habits"""
    #     if self.df is None:
    #         return None
            
    #     # Convert boolean columns to numeric
    #     habit_data = self.df.copy()
    #     for col in config.BOOLEAN_VARIABLES:
    #         if col in habit_data.columns:
    #             habit_data[col] = habit_data[col].fillna(False) # replace NA with 0
    #             habit_data[col] = habit_data[col].astype(int) # convert from boolean to int

    #     # Add period data
    #     period_data = habit_data[['Date', 'Period']].copy()
    #     period_data['Variable'] = 'Period'
    #     period_data = period_data.rename(columns={'Period': 'Value'})

    #     # Prepare habit data
    #     habit_data = habit_data.melt(
    #         id_vars=['Date'],
    #         value_vars=config.BOOLEAN_VARIABLES,
    #         var_name='Variable',
    #         value_name='Value'
    #     )

    #     # Combine data
    #     all_data = pd.concat([habit_data, period_data])

    #     # Apply color coding
    #     def get_value_category(row):
    #         if row['Variable'] in ['Math', 'Sex', 'O', 'Period']:
    #             return -2 if row['Value'] == 1 else 0
    #         elif row['Variable'] in ['Caffeine', 'Alcohol', 'Weed', 'Delta8']:
    #             return -1 if row['Value'] == 1 else 0
    #         else:
    #             return 1 if row['Value'] == 1 else 0
                
    #     all_data['Category'] = all_data.apply(get_value_category, axis=1)

    #     # Filter by start date
    #     if start_date:
    #         all_data[all_data['Date'] >= pd.to_datetime(start_date).date()]

    #     # Create heatmap
    #     plt.figure(figsize=(15, 10))

    #     pivot_table = all_data.pivot_table(
    #         index='Date',
    #         columns='Variable',
    #         values='Category',
    #         aggfunc='sum'
    #     )

    #     # Custom colormap
    #     colors = ['pink', 'red', 'white', 'green']
    #     cmap = LinearSegmentedColormap.from_list('custom', colors)

    #     sns.heatmap(
    #         pivot_table,
    #         cmap=cmap,
    #         cbar=True,
    #         xticklabels=True,
    #         yticklabels=True,
    #         center=0
    #     )

    #     plt.title('Daily Habit Tracker')
    #     plt.xticks(rotation=90)
    #     plt.tight_layout()
    #     # return plt.gcf()
