import schedule
import time
import subprocess
from threading import Thread

# --- Funciones para correr los scripts ---
def run_analysis():
    print("🔁 Running: technical_analysis.py + check_entry.py")
    subprocess.run(["python", "python/technical_analysis.py"])
    subprocess.run(["python", "python/check_entry.py"])

def run_prediction_check():
    print("🔁 Running: check_prediction.py")
    subprocess.run(["python", "python/check_prediction.py"])

# --- Scheduler ---
def run_scheduler():
    # Ejecuta inmediatamente al inicio
    run_analysis()

    # Programa cada 15 minutos y cada 4 horas
    schedule.every(15).minutes.do(run_analysis)
    schedule.every(4).hours.do(run_prediction_check)

    while True:
        schedule.run_pending()
        time.sleep(10)

# --- Main ---
if __name__ == "__main__":
    # Inicia el scheduler en segundo plano
    t = Thread(target=run_scheduler)
    t.start()

    # Lanza el dashboard
    subprocess.run(["streamlit", "run", "python/dashboard.py"])