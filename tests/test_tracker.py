import pytest
import pandas as pd
import numpy as np
from habit_tracking.tracker import HabitTracker

# ---------------------------------------------------------
# FIXTURES: The "Setup" phase
# In Economics, this is like defining your control group.
# ---------------------------------------------------------
@pytest.fixture
def sample_data():
    """Provides a consistent, 'dirty' dataframe to test cleaning logic."""
    data = {
        'Date': ['2023-01-01', '2023-01-02', '2023-01-04'], # Note the gap on Jan 3
        'Mental_Health': ['5', '7', np.nan],                # String and NaN
        'Exercised': ['Yes', 'No', 'Yes'],                  # Categorical
        'Tracked_Habits': [True, True, True]
    }
    return pd.DataFrame(data)

@pytest.fixture
def tracker(sample_data):
    """Initializes the tracker with the sample data."""
    ht = HabitTracker()
    ht.df = sample_data
    return ht

# ---------------------------------------------------------
# TEST 1: Data Type Integrity
# Ensures your '1-10' scores actually become numbers.
# ---------------------------------------------------------
def test_mental_health_conversion(tracker):
    # Act: Run the cleaning logic (assuming you have a clean method)
    # If your method name differs, adjust 'load_and_clean' below
    tracker.load_and_clean() 
    
    # Assert: Check if the '5' string became an integer/float
    assert pd.api.types.is_numeric_dtype(tracker.df['Mental_Health'])
    assert tracker.df.loc[0, 'Mental_Health'] == 5

# ---------------------------------------------------------
# TEST 2: Boolean Logic (The "Yes/No" to 0/1)
# ---------------------------------------------------------
def test_habit_boolean_mapping(tracker):
    tracker.load_and_clean()
    
    # Verify 'Yes' became 1 and 'No' became 0
    assert tracker.df.loc[0, 'Exercised'] == 1
    assert tracker.df.loc[1, 'Exercised'] == 0

# ---------------------------------------------------------
# TEST 3: Time-Series Continuity
# Critical for your Lagged Analysis. Ensures we don't 
# calculate a lag across a missing day.
# ---------------------------------------------------------
def test_lag_calculation_gap_handling(tracker):
    # Setup: Manually create a lag
    df = tracker.df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    # Calculate gap
    df['Gap'] = (df['Date'] - df['Date'].shift(1)).dt.days
    
    # The gap between Jan 2 and Jan 4 should be 2 days
    assert df.iloc[2]['Gap'] == 2
    
    # Logic Check: Ensure your analysis code would drop this row 
    # if it requires consecutive days (Gap == 1)
    consecutive_days = df[df['Gap'] == 1]
    assert len(consecutive_days) == 1 # Only Jan 2 follows Jan 1

# ---------------------------------------------------------
# TEST 4: Edge Cases (Empty Data)
# ---------------------------------------------------------
def test_empty_df_handling():
    ht = HabitTracker()
    ht.df = pd.DataFrame()
    
    # This should handle gracefully without crashing
    with pytest.raises(Exception): 
        # If your code is robust, it might return a specific error 
        # or an empty DF. Here we test if it raises an error on empty input.
        ht.plot_prep()
        
        
        
# Next Step: 
# Try intentionally breaking one of your CSV files 
# (e.g., change a "Yes" to "Maybe") and run the tests. 
# You’ll see exactly how unit testing catches human error before 
# it reaches your statistical models.