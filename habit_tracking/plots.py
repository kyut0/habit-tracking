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
import matplotlib.cm as cm
from matplotlib.lines import Line2D
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
    
    def plot_prep(self):
        """Run all necessary data preparation steps for plotting"""
        self.convert_df_to_long()
        self.filter_dates()
        self.aggregate_monthly_stats()
    
    def plot_all(self):
        """Generate all plots"""
        self.plot_prep()
        
        self.plot_total_barchart()
        self.plot_mental_health_trend()
        self.plot_monthly_percentages()
        # self.plot_sleep_pattern() # NEED TO FIX DATETIME HANDLING FOR SLEEP PLOT
        
        # self.plot_cumulative_habits()
        # self.plot_monthly_summary(year_month='2024-05')
        # self.plot_monthly_heatmap()
        # self.plot_sleep_quality()
        # self.plot_weight_trends()
        # self.plot_goal_heatmap()
    
    def convert_df_to_long(self):
        """Convert self.df to long format for easier plotting"""
        if self.df is None:
            return None
            
        self.df_long = pd.melt(self.df, id_vars=['Date'], value_vars=self.boolean_variables,
                               var_name='Habit', value_name='Value')   
        
        # Split date into year, month, day
        self.df_long['Year'] = pd.to_datetime(self.df_long['Date']).dt.year
        self.df_long['Month'] = pd.to_datetime(self.df_long['Date']).dt.month
        # self.df_long['Day'] = pd.to_datetime(self.df_long['Date']).dt.day
        
        # Create year-month column
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
            self.df_long = self.df_long[self.df_long['Date'] >= pd.to_datetime(start_date)]
            self.df = self.df[self.df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            self.df_long = self.df_long[self.df_long['Date'] <= pd.to_datetime(end_date)]
            self.df = self.df[self.df['Date'] <= pd.to_datetime(end_date)]
    
    def aggregate_monthly_stats(self):
        """Aggregate daily data to monthly statistics (percentages & counts)"""
        if self.df_long is None:
            return None
            
        # Calculate monthly percentages
        self.df_monthly_perc = self.df_long.groupby(['Year_Month', 'Habit'])['Value'].mean().reset_index()
        self.df_monthly_perc['Percentage'] = self.df_monthly_perc['Value'] * 100
        self.df_monthly_perc = self.df_monthly_perc.drop(columns=['Value'])
        
        # Calculate monthly counts
        self.df_monthly_raw = self.df_long.groupby(['Year_Month', 'Habit'])['Value'].sum().reset_index()
        self.df_monthly_raw = self.df_monthly_raw.rename(columns={'Value': 'Count'})
    
    def plot_cumulative_habits(self):
        """Plot cumulative habits over time"""
        plt.figure(figsize=(15, 8))
        
        # Plot each variable, starting from its first non-null observation
        for var in self.boolean_variables:
            var_data = self.df[['Date', var]].dropna(subset=[var])
            cumsum = var_data[var].cumsum()
            plt.plot(var_data['Date'], cumsum,
                    label=var, color=config.VAR_COLORS.get(var, 'gray'))
            
        plt.title('Cumulative Habits Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Days')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
    def plot_monthly_percentages(self):
        """Plot monthly percentages of habits over time"""
        df_long = self.df_monthly_perc.copy()

        plt.figure(figsize=(15, 8))
        
        for var in self.boolean_variables:
            var_data = df_long[df_long['Habit'] == var]
            plt.plot(var_data['Year_Month'], 
                    var_data['Percentage'], 
                    label=var, color=config.VAR_COLORS.get(var, 'gray'))
        
        plt.title('Monthly Percentages of Habits')
        plt.xlabel('Month')
        plt.ylabel('Percentage (%)')
        plt.xticks(rotation=90)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
    
    def plot_total_barchart(self):
        """Plot total counts of habits as a bar chart"""
        df_long = self.df_long.copy()
        total_counts = df_long.groupby('Habit')['Value'].sum().reset_index()
        total_counts = total_counts.sort_values(by='Value', ascending=False)

        plt.figure(figsize=(12, 6))
        plt.bar(total_counts['Habit'], total_counts['Value'],
                color=total_counts['Habit'].map(config.VAR_COLORS).fillna('gray'))
        
        plt.title('Total Counts of Habits')
        plt.xlabel('Habit')
        plt.ylabel('Total Count')
        plt.xticks(rotation=90)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
    
    def plot_monthly_summary(self, year_month=None):
        """Plot a summary of monthly statistics (percentages) for a single year-month (e.g. '2023-06')"""
        df_long = self.df_monthly_perc.copy()

        if year_month:
            df_long = df_long[
                df_long['Year_Month'] == year_month
            ]
            
        df_long = df_long.sort_values(by='Percentage', ascending=False)

        plt.figure(figsize=(15, 10))
        
        plt.bar(df_long['Habit'], df_long['Percentage'],
                color=df_long['Habit'].map(config.VAR_COLORS).fillna('gray'))

        title = f'Monthly Summary of Habits — {year_month}' if year_month else 'Monthly Summary of Habits'
        plt.title(title)
        plt.xlabel('Habit')
        plt.ylabel('Percentage (%)')
        plt.xticks(df_long['Habit'], rotation=90)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
    def plot_mental_health_trend(self):
        """Plot mental health trend over time"""
        plt.figure(figsize=(15, 6))
        
        mental_health = self.df[['Date', 'Mental_Health']].copy()
        
        plt.plot(mental_health['Date'], 
                mental_health['Mental_Health'],
                color='grey',
                alpha=0.5)
        
        # Add smoothed trend line
        window_size = 30  # Adjust as needed
        rolling_mean = mental_health['Mental_Health'].rolling(window=window_size, center=True, min_periods=1).mean()
        plt.plot(mental_health['Date'], rolling_mean, color='black', linewidth=2)
        
        plt.title('Mental Health Over Time')
        plt.xlabel('Date')
        plt.xticks(rotation=90)
        plt.ylabel('Mental Health Score (1-10)')
        plt.grid(True, alpha=0.3)
        
    def plot_monthly_heatmap(self):
        """Plot a heatmap of monthly statistics"""
        heatmap_data = self.df_monthly_perc.copy()

        # Create heatmap
        plt.figure(figsize=(15, 10))
        pivot_table = heatmap_data.pivot(
            index='Year_Month',
            columns='Habit',
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

    def plot_medications(self):
        """Plot medication usage over time"""
        if self.meds_data is None:
            return None
            
        meds_data = self.meds_data.copy()
        
        # Create a unique list of medication types
        unique_meds = meds_data['Medication_Generic'].unique()

        # Generate a color palette (using 'tab10' or 'Set1' for distinct colors)
        colors = cm.get_cmap('tab10', len(unique_meds))
        color_map = {med: colors(i) for i, med in enumerate(unique_meds)}

        # Map the column to these colors
        med_colors = meds_data['Medication_Generic'].map(color_map)

        # Plot
        plt.figure(figsize=(15, 10))
        plt.hlines(
            y=meds_data['Dose (mg)'],
            xmin=meds_data['Start_Date'],
            xmax=meds_data['End_Date'],
            colors=med_colors, # Note: plt.hlines uses 'colors' (plural) for sequences
            alpha=0.6,
            linewidth=3
        )
        
        plt.title('Medication Usage Over Time')
        plt.xlabel('Date')
        plt.ylabel('Dose (mg)')
        plt.xticks(rotation=90)
        plt.grid(True, alpha=0.3)
        
        legend_elements = [Line2D([0], [0], color=color_map[med], lw=4, label=med) 
                        for med in unique_meds]
        plt.legend(handles=legend_elements, title="Medication", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

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
        
    def plot_goal_heatmap(self, start_date=None):
        """Plot a heatmap showing goal achievement"""
        monthly_stats = self.df_monthly_perc.copy()
        
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
