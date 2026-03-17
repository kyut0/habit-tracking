# Load packages
from googleapiclient.discovery import build
from google.oauth2 import service_account
import io
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

from habit_tracking import config
from habit_tracking.plots import HabitPlotter

class HabitTracker(HabitPlotter):
    def __init__(self):
        self.df = None
        self.sleep_data = None
        self.weight_data = None

    def load_google_sheets_data(self, service_account_file, spreadsheet_id):
        """Load data from Google Sheets"""
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        service = build('drive', 'v3', credentials=credentials)
        request = service.files().export_media(
            fileId=spreadsheet_id,
            mimeType='text/csv'
        )
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        fh.seek(0)
        return pd.read_csv(fh)

    def load_and_clean(self, service_account_file, spreadsheet_id, sleep_file=None, weight_file=None):
        """Load and clean all data sources"""
        # Load main tracking data
        df_raw = self.load_google_sheets_data(service_account_file, spreadsheet_id)
        
        # Clean column names
        self.df = df_raw.rename(columns=config.CLEAN_COLUMN_NAMES)
        
        # Cleaning and processing functions
        self.clean_dates()
        self.process_boolean_variables()
        self.process_categorical_variables()
        self.calculate_tracked_habits()
        # period_dates = self.process_periods() # DO SOMETHING WITH THIS--RETURN OR ADD TO SELF __INIT__
        
        # Load additional data if provided
        if sleep_file:
            self.sleep_data = pd.read_csv(sleep_file)
            self.process_sleep_data()
        if weight_file:
            self.weight_data = pd.read_csv(weight_file)
            self.clean_weight_data()
            
    def clean_dates(self):
        """Clean and process dates in the dataframe"""
        
        # Fill missing dates with Submission_DateTime
        self.df['Date'] = self.df.apply(
            lambda row: pd.to_datetime(row['Submission_DateTime'])
            if pd.isna(row['Date']) else pd.to_datetime(row['Date']),
            axis=1
        )

        # Convert from datetime to date
        self.df['Date'] = self.df['Date'].dt.date

        # Create complete date range
        date_range = pd.date_range(
            start=config.EXERCISE_START_DATE,  # Original start date from R code
            end=pd.Timestamp.today().date(),
            freq='D'
        )

        # Create a dataframe with all dates
        all_dates = pd.DataFrame({'Date': date_range})

        # Convert from datetime to date
        all_dates['Date'] = all_dates['Date'].dt.date

        # Merge with existing data
        self.df = pd.merge(all_dates, self.df, on='Date', how='left')
        
    def process_boolean_variables(self):
        """Convert Yes/No to boolean and handle missing values"""
        for col in config.BOOLEAN_VARIABLES:
            self.df[col] = self.df[col].map({'Yes': True, 'No': False})
            self.df[col] = self.df[col].astype('boolean')
            
    def process_categorical_variables(self):
        """Convert categorical variables to proper types"""
        
        # Libido as ordered category
        self.df['Libido'] = pd.Categorical(
            self.df['Libido'].map({'N/A': 'None', 'Moderate': 'Medium', 'High': 'High'}),
            categories=['None', 'Medium', 'High'],
            ordered=True
        )
        
        # Skin as ordered category
        self.df['Skin'] = pd.Categorical(
            self.df['Skin'],
            categories=['Major breakouts', 'Minor breakouts', 'Clear'],
            ordered=True
        )
        
    def calculate_tracked_habits(self):
        """Calculate whether habits were tracked each day"""
        self.df['Tracked_Habits'] = (
            pd.to_datetime(self.df['Submission_DateTime']).dt.date == 
            pd.to_datetime(self.df['Date']).dt.date
        )
        
        self.df['Collected_Data'] = ~self.df['Submission_DateTime'].isna()
        
    def process_sleep_data(self):
        """Process sleep data if available"""
        if self.sleep_data is None:
            return
            
        # Clean sleep data columns
        sleep_clean = self.sleep_data.rename(columns=config.CLEAN_SLEEP_COLUMNS)
        
        # Convert time columns
        sleep_clean['Time_in_Bed_hr'] = sleep_clean['Time_in_Bed_sec'] / 3600
        sleep_clean['Time_Asleep_hr'] = sleep_clean['Time_Asleep_sec'] / 3600
        sleep_clean['Time_Before_Sleep_hr'] = sleep_clean['Time_Before_Sleep_sec'] / 3600
        
        sleep_clean['Date'] = pd.to_datetime(sleep_clean['Sleep_Start'].str.split(' ').str[0]).dt.date 
        sleep_clean['Sleep_Start_Time'] = sleep_clean['Sleep_Start'].str.split(' ').str[1]
        sleep_clean['Sleep_End_Time'] = sleep_clean['Sleep_End'].str.split(' ').str[1]
        
        # Remove bad data points
        sleep_clean = sleep_clean[~sleep_clean['Date'].isin(config.BAD_SLEEP_DATES)]
        
        # Create complete date range
        date_range = pd.date_range(
            start='2020-07-28',  # Original start date from R code
            end='2024-07-15', # pd.Timestamp.today().date()
            freq='D'
        )

        # Create a dataframe with all dates
        all_dates = pd.DataFrame({'Date': date_range})

        # Convert from datetime to date
        all_dates['Date'] = all_dates['Date'].dt.date

        # Merge with existing data
        sleep_clean_all = pd.merge(all_dates, sleep_clean, on='Date', how='left')
        
        # Convert time columns to hour as float
        def time_to_hour(t):
            return pd.to_datetime(t).hour + pd.to_datetime(t).minute / 60
        
        sleep_clean_all['Start_Hour'] = sleep_clean_all['Sleep_Start_Time'].apply(time_to_hour) 
        sleep_clean_all['End_Hour'] = sleep_clean_all['Sleep_End_Time'].apply(time_to_hour) 
        
        # Update self
        self.sleep_data = sleep_clean_all
        
    def clean_weight_data(self):
        """Clean and process the weight tracking data"""
        if self.weight_data is None:
            return False
            
        # Clean headers
        self.weight_data = self.weight_data.rename(columns=config.CLEAN_WEIGHT_COLUMNS)
        
        # Convert datetime
        self.weight_data['Submission_DateTime'] = pd.to_datetime(self.weight_data['Submission_DateTime'])
        self.weight_data['Date'] = self.weight_data['Submission_DateTime'].dt.date
        
        return True
    
    def process_periods(self):
        """Process period data to get start and end dates"""
        if self.df is None:
            return None
            
        # Create a copy of period data
        periods = self.df[['Date', 'Period']].copy()
        
        # Calculate changes in period status
        periods['Binary_Start_End'] = periods['Period'].fillna(0).diff()
        
        # Get start dates (where Binary_Start_End == 1)
        starts = periods[periods['Binary_Start_End'] == 1]['Date']
        
        # Get end dates (day before Binary_Start_End == -1)
        ends = periods[periods['Binary_Start_End'] == -1]['Date'].apply(
            lambda x: x - timedelta(days=1)
        )
        
        # Combine into DataFrame
        period_dates = pd.DataFrame({
            'start': starts.values,
            'end': ends.values
        })
        
        return period_dates
    
    def calculate_monthly_stats(self):
        """Calculate monthly statistics"""
        # Extract month and year
        self.df['Month'] = pd.to_datetime(self.df['Date']).dt.strftime('%m')
        self.df['Year'] = pd.to_datetime(self.df['Date']).dt.strftime('%Y')
        
        # Calculate raw counts
        monthly_stats_raw = self.df.groupby(['Year', 'Month'])[config.BOOLEAN_VARIABLES].sum()
        
        # Calculate percentages
        monthly_stats_percent = (
            self.df.groupby(['Year', 'Month'])[config.BOOLEAN_VARIABLES].sum() / 
            self.df.groupby(['Year', 'Month'])[config.BOOLEAN_VARIABLES].count() * 100
        )
        
        # Convert 'Mental_Health' to numeric (if not already)
        self.df['Mental_Health'] = pd.to_numeric(self.df['Mental_Health'], errors='coerce')
        
        # Add mental health average
        mental_health_avg = self.df.groupby(['Year', 'Month'])['Mental_Health'].mean()
        monthly_stats_raw['Mental_Health'] = mental_health_avg
        monthly_stats_percent['Mental_Health'] = mental_health_avg * 10
        
        return monthly_stats_raw, monthly_stats_percent

        
    
