# Load packages
from googleapiclient.discovery import build
from google.oauth2 import service_account
import io
from googleapiclient.http import MediaIoBaseDownload
from numpy.__config__ import CONFIG
import pandas as pd
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

from habit_tracking import config
from habit_tracking.plots import HabitPlotter

class HabitTracker(HabitPlotter):
    def __init__(self):
        self.df = None
        
        self.df_long = None
        
        self.df_monthly_perc = None
        self.df_monthly_raw = None
        
        self.period_dates = None
        
        self.sleep_data = None
        self.weight_data = None
        
        self.meds_data = None

    def load_google_sheets_data(self, service_account_file, spreadsheet_id):
        """Load data from Google Sheets"""
        if isinstance(service_account_file, str):
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
        else:
            credentials = service_account_file
        
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

    def load_and_clean(self, 
                       service_account_file=config.SERVICE_ACCOUNT_FILE, 
                       spreadsheet_id=config.HT_ID, 
                       meds_id=config.MEDS_ID,
                       sleep_file="/Users/katyyut/Desktop/01_Code/GitHub/habit-tracking/data/raw/20240716_Sleep_Data.csv", 
                       weight_file="/Users/katyyut/Desktop/01_Code/GitHub/habit-tracking/data/raw/20230911_Weight_Data.csv"):
        """Load and clean all data sources"""
        # Load main tracking data
        df_raw = self.load_google_sheets_data(service_account_file, spreadsheet_id)
        
        # Clean column names
        self.df = df_raw.rename(columns=config.CLEAN_COLUMN_NAMES)
        
        # Cleaning and processing functions
        self.fill_dates()
        self.populate_daily_range()
        self.calculate_tracked_habits()
        self.process_boolean_variables()
        self.process_categorical_variables()
        self.combine_d8_weed() # if config.COMBINE_D8_WEED is True, this will combine the two variables into one
        self.process_periods()
        
        # Load additional data if provided
        if sleep_file:
            self.sleep_data = pd.read_csv(sleep_file)
            self.process_sleep_data()
        if weight_file:
            self.weight_data = pd.read_csv(weight_file)
            self.clean_weight_data()
            
        # Medications 
        self.load_and_clean_meds_data(service_account_file, meds_id)
            
    def fill_dates(self):
        """Populate missing dates in the main tracking data using Submission_DateTime"""
        
        # Fill missing dates with Submission_DateTime
        self.df['Date'] = self.df.apply(
            lambda row: pd.to_datetime(row['Submission_DateTime'])
            if pd.isna(row['Date']) else pd.to_datetime(row['Date']),
            axis=1
        )

        # Convert from datetime to date
        self.df['Date'] = self.df['Date'].dt.date

    def populate_daily_range(self, df=None, start_date=None, end_date=None):
        """Ensure there is a row for every date in the range, filling missing dates with NaN values.

        If df is None, operates on self.df in place.
        If df is provided, returns a new dataframe with the full date range.
        start_date and end_date override the min/max from the dataframe.
        """
        target = self.df if df is None else df

        start = start_date if start_date is not None else target['Date'].min()
        end = end_date if end_date is not None else target['Date'].max()

        all_dates = pd.DataFrame({'Date': pd.date_range(start=start, end=end, freq='D').normalize()})

        target = target.copy()
        target['Date'] = pd.to_datetime(target['Date'])

        result = pd.merge(all_dates, target, on='Date', how='left')
        result['Date'] = result['Date'].dt.date

        if df is None:
            self.df = result
        else:
            return result
        
    def process_boolean_variables(self):
        """Convert Yes/No to boolean and handle missing values"""        
        for col in self.boolean_variables:
            if col not in config.BOOLEAN_VARIABLES_COMPUTED:
                self.df[col] = self.df[col].map({'Yes': True, 'No': False})
            self.df[col] = self.df[col].astype('boolean')
            
            # Fill missing values with config.NA_AS_TRUE if specified
            if col in config.NA_AS_TRUE:
                fill_value = config.NA_AS_TRUE[col]
                if fill_value:
                    # Before the first real observation, assume False (habit not yet tracked)
                    # After the first real observation, assume True (NA means habit was done)
                    first_real = self.df[col].first_valid_index()
                    self.df.loc[:first_real, col] = self.df.loc[:first_real, col].fillna(False)
                    self.df[col] = self.df[col].fillna(True)
                else:
                    self.df[col] = self.df[col].fillna(False)
            
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
        
    def combine_d8_weed(self):
        """Combine Delta8 and Weed into a single variable if config.COMBINE_D8_WEED is True"""
        if not config.COMBINE_D8_WEED:
            return
        
        self.df['Weed'] = self.df.apply(
            lambda row: row['Weed'] or row['Delta8'], 
            axis=1
        )
        
        self.df.drop(columns=['Delta8'], inplace=True)
        
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
        
        sleep_clean['Date'] = pd.to_datetime(sleep_clean['Sleep_Start'].str.split(' ').str[0]).dt.date # I THINK THIS IS WRONG. COMPARE TO R CODE.
        sleep_clean['Sleep_Start_Time'] = sleep_clean['Sleep_Start'].str.split(' ').str[1]
        sleep_clean['Sleep_End_Time'] = sleep_clean['Sleep_End'].str.split(' ').str[1]
        
        # Remove bad data points
        sleep_clean = sleep_clean[~sleep_clean['Date'].isin(config.BAD_SLEEP_DATES)]
        
        sleep_clean_all = self.populate_daily_range(
            df=sleep_clean,
            start_date='2020-07-28', 
            end_date='2024-07-15',    
        )
        
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
        periods['Binary_Start_End'] = periods['Period'].astype(int).diff()

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
        
        self.period_dates = period_dates
        
    def load_and_clean_meds_data(self, service_account_file, meds_id):
        """Load and clean medications data"""
        
        meds_data = self.load_google_sheets_data(service_account_file, meds_id)
        
        # Convert to datetime first (stay in datetime64[ns] format)
        meds_data['Start_Date'] = pd.to_datetime(meds_data['Start_Date'])
        meds_data['End_Date'] = pd.to_datetime(meds_data['End_Date'], errors='coerce')
        
        # Fill the NaT values while they are still Datetime objects
        # Note: inplace=True is being deprecated in newer pandas; assignment is safer.
        meds_data['End_Date'] = meds_data['End_Date'].fillna(pd.Timestamp('today'))
        
        # Finally, convert both to date objects if you need the YYYY-MM-DD format
        meds_data['Start_Date'] = meds_data['Start_Date'].dt.date
        meds_data['End_Date'] = meds_data['End_Date'].dt.date
        
        self.meds_data = meds_data
    
    def calculate_monthly_stats(self):
        """Calculate monthly statistics"""
        # Extract month and year
        self.df['Month'] = pd.to_datetime(self.df['Date']).dt.strftime('%m')
        self.df['Year'] = pd.to_datetime(self.df['Date']).dt.strftime('%Y')
        
        # Calculate raw counts
        monthly_stats_raw = self.df.groupby(['Year', 'Month'])[self.boolean_variables].sum()
        
        # Calculate percentages
        monthly_stats_percent = (
            self.df.groupby(['Year', 'Month'])[self.boolean_variables].sum() / 
            self.df.groupby(['Year', 'Month'])[self.boolean_variables].count() * 100
        )
        
        # Convert 'Mental_Health' to numeric (if not already)
        self.df['Mental_Health'] = pd.to_numeric(self.df['Mental_Health'], errors='coerce')
        
        # Add mental health average
        mental_health_avg = self.df.groupby(['Year', 'Month'])['Mental_Health'].mean()
        monthly_stats_raw['Mental_Health'] = mental_health_avg
        monthly_stats_percent['Mental_Health'] = mental_health_avg * 10
        
        return monthly_stats_raw, monthly_stats_percent

        
    
