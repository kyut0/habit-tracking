from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
print(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# CONSTANTS ===============================================
# Key dates
EXERCISE_START_DATE = '2018-10-22'
HT_START_DATE = '2022-06-17'
SLEEP_REFRESH_DATE = '2024-07-16'

BAD_SLEEP_DATES = [
    '2021-09-14',
    '2023-11-20',
    '2024-02-26'
]

# Constants
BOOLEAN_VARIABLES = [
    'Made_Bed', 'Exercised', 'Stretched', 'Danced', 'Morning_Pages', 
    'Mindfulness', 'Caffeine', 'Alcohol', 'Weed', 'Delta8', 'Sex', 
    'Math', 'O', 'Period', 
    #'Tracked_Habits', 'Collected_Data', 
    # tracked_habits and collected_data are not in the data, they're calculated in the code
]

VAR_COLORS = {
    'Caffeine': 'brown',
    'Weed': 'darkgreen',
    'Delta8': 'green',
    'Exercised': 'blue',
    'Stretched': 'lightblue',
    'Made_Bed': 'darkorange',
    'Morning_Pages': 'tan',
    'Mindfulness': 'white',
    'Danced': 'purple',
    'Alcohol': 'yellow',
    'Sex': 'red',
    'Math': 'pink',
    'O': 'gold',
    'Tracked_Habits': 'black',
    'Collected_Data': 'grey'
}

CLEAN_COLUMN_NAMES = {
    'Timestamp': 'Submission_DateTime',
    'Date': 'Date',
    'Made bed?': 'Made_Bed',
    'Exercise?': 'Exercised',
    'Stretch?': 'Stretched',
    'Dance?': 'Danced',
    'Morning pages?': 'Morning_Pages',
    'Mindfulness?': 'Mindfulness',
    'Cold plunge?': 'Cold_Plunge',
    'Caffeine?': 'Caffeine',
    'Caffeine Quantity, mg': 'Caffeine_Quantity_mg',
    'Alcohol?': 'Alcohol',
    'Weed?': 'Weed',
    'Delta 8?': 'Delta8',
    'Sex?': 'Sex',
    'Math?': 'Math',
    'O?': 'O',
    'Libido': 'Libido',
    'Period?': 'Period',
    'Skin': 'Skin',
    'Hair care': 'Hair_Care',
    'Mental health': 'Mental_Health',
    'Other/notes:': 'Other_notes'
}

# Month dictionary
MONTHS = {
    '01': 'January',
    '02': 'February',
    '03': 'March',
    '04': 'April',
    '05': 'May',
    '06': 'June',
    '07': 'July',
    '08': 'August',
    '09': 'September',
    '10': 'October',
    '11': 'November',
    '12': 'December'
}

CLEAN_SLEEP_COLUMNS = {
    'Start': 'Sleep_Start',
    'End': 'Sleep_End',
    'Sleep Quality': 'Sleep_Quality',
    'Movements per hour': 'Movements_per_Hour',
    'Time in bed (seconds)': 'Time_in_Bed_sec',
    'Time asleep (seconds)': 'Time_Asleep_sec',
    'Time before sleep (seconds)': 'Time_Before_Sleep_sec',
    'Snore time': 'Snore_Time'
}

CLEAN_WEIGHT_COLUMNS = {
    'Time of Measurement': 'Submission_DateTime',
    'Weight(lb)': 'Weight_lb',
    'Body Fat(%)': 'Body_Fat',
    'Fat-free Body Weight(lb)': 'Fatfree_Bodyweight_lb',
    'Subcutaneous Fat(%)': 'Subcutaneous_Fat',
    'Visceral Fat': 'Visceral_Fat',
    'Body Water(%)': 'Body_Water',
    'Skeletal Muscle(%)': 'Skeletal_Muscle',
    'Muscle Mass(lb)': 'Muscle_Mass_lb',
    'Bone Mass(lb)': 'Bone_Mass_lb',
    'Protein(%)': 'Protein',
    'BMR(kcal)': 'BMR_kcal',
    'Metabolic Age': 'Metabolic_Age'
}
