import schedule
import time
import subprocess
from threading import Thread
import os

# --- Run initial setup script ---
def run_shell_script(script_path):
    print(f"🔧 Running setup script: {script_path}")
    try:
        subprocess.run(["bash", script_path], check=True)
        print("✅ Setup completed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup script failed: {e}")

# --- Functions to run core scripts ---
def run_analysis():
    print("🔁 Running: technical_analysis.py + check_entry.py")
    subprocess.run(["python", "python/technical_analysis.py"])
    subprocess.run(["python", "python/check_entry.py"])

def run_prediction_check():
    print("🔁 Running: check_prediction.py")
    subprocess.run(["python", "python/check_prediction.py"])

# --- Scheduler setup ---
def run_scheduler():
    run_analysis()  # run once immediately

    schedule.every(15).minutes.do(run_analysis)
    schedule.every(4).hours.do(run_prediction_check)

    while True:
        schedule.run_pending()
        time.sleep(10)

# --- Main service entrypoint ---
if __name__ == "__main__":
    # STEP 0: Run shell setup script first
    run_shell_script("bash/set-up.sh")

    # STEP 1: Start scheduled background task
    t = Thread(target=run_scheduler)
    t.start()

    # STEP 2: Launch Streamlit dashboard
    subprocess.run(["streamlit", "run", "python/dashboard.py"])