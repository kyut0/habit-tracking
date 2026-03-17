from habit_tracking.tracker import HabitTracker
import argparse

# TO RUN:
# python -m habit_tracking --ssid 1LyIl8YRyw8nwP2TWBFAw-oRvDU9xnqj1BRVglntLNrU --creds /Users/katyyut/Desktop/01_Code/GitHub/habit-tracking/habit-tracking-python-379e261c6b6d.json --sleep data/raw/20240716_Sleep_Data.csv --weight data/raw/20230911_Weight_Data.csv

def main(ssid: str, creds: str, sleep_file: str, weight_file: str):
    tracker = HabitTracker()

    tracker.apply_cleaning(
        service_account_file=creds,
        spreadsheet_id=ssid,
        sleep_file=sleep_file,
        weight_file=weight_file
    )
    
    print("Success!")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Run the habit tracking application.")
    parser.add_argument("--ssid", type=str, required=True, help="Google Drive spreadsheet ID.")
    parser.add_argument("--creds", type=str, required=True, help="Path to the Google Drive service account credentials JSON file.")
    parser.add_argument("--sleep", type=str, required=False, help="Path to the sleep data CSV file.")
    parser.add_argument("--weight", type=str, required=False, help="Path to the weight data CSV file.")
    
    args = parser.parse_args()
    
    main(ssid=args.ssid, 
         creds=args.creds,
         sleep_file=args.sleep,
         weight_file=args.weight)