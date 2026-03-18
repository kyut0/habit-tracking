from habit_tracking.tracker import HabitTracker
import argparse

# TO RUN:
# python -m habit_tracking 

def main(ssid: str, creds: str, sleep_file: str, weight_file: str):
    tracker = HabitTracker()

    tracker.load_and_clean()
    
    print("Success!")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Run the habit tracking application.")
    parser.add_argument("--ssid", type=str, required=False, help="Google Drive spreadsheet ID.")
    parser.add_argument("--creds", type=str, required=False, help="Path to the Google Drive service account credentials JSON file.")
    parser.add_argument("--sleep", type=str, required=False, help="Path to the sleep data CSV file.")
    parser.add_argument("--weight", type=str, required=False, help="Path to the weight data CSV file.")
    
    args = parser.parse_args()
    
    main(ssid=args.ssid, 
         creds=args.creds,
         sleep_file=args.sleep,
         weight_file=args.weight)