# Habit Tracking Analysis

Python implementation of habit tracking data analysis, converted from R.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Sheets API:
   - Create a Google Cloud project
   - Enable the Google Sheets API
   - Create a service account and download the JSON credentials
   - Save the credentials file securely
   - Share your Google Sheet with the service account email

3. Update the configuration in the script:
   - Set `SERVICE_ACCOUNT_FILE` to point to your credentials JSON file
   - Set `SPREADSHEET_ID` to your Google Sheet's ID
   - Update file paths for sleep, weight, and exercise data if needed

## Usage

```python
from habit_tracking import HabitTracker

# Initialize tracker
tracker = HabitTracker()

# Load data
tracker.load_data(
    service_account_file='path/to/credentials.json',
    spreadsheet_id='your-spreadsheet-id',
    sleep_file='sleep_data.csv',
    weight_file='weight_data.csv',
    exercise_file='exercise_log.csv'
)

# Process data
tracker.clean_dates()
tracker.process_boolean_variables()
tracker.process_categorical_variables()
tracker.calculate_tracked_habits()

# Calculate statistics
monthly_raw, monthly_percent = tracker.calculate_monthly_stats()

# Generate visualizations
tracker.plot_cumulative_habits()
tracker.plot_mental_health_trend()
plt.show()
```

## Features

- Data loading from Google Sheets and CSV files
- Comprehensive data cleaning and preprocessing
- Boolean and categorical variable processing
- Monthly statistics calculation
- Visualization of habits and trends
- Sleep data processing
- Mental health tracking

## Data Structure

The code expects the following data structure in your Google Sheet:

Required columns:
- Timestamp
- Date
- Made bed?
- Exercise?
- Stretch?
- Dance?
- Morning pages?
- Mindfulness?
- Caffeine?
- Alcohol?
- Weed?
- Delta 8?
- Sex?
- Math?
- O?
- Mental health
- Period?
- Other/notes:

Optional data files:
- Sleep data CSV
- Weight data CSV
- Exercise log CSV

## Contributing

Feel free to submit issues and enhancement requests! 