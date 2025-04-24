import subprocess
from datetime import datetime
import time
import os

def run_script(path):
    print(f"▶️ Ejecutando: {path}")
    subprocess.run(["python", path])

def main():
    print(f"\n🕐 Iniciando análisis completo a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    run_script("python/technical_analysis.py")
    run_script("python/check_entry.py")

    print("\n⏳ Esperando 12h para evaluar predicciones...")
    #time.sleep(12 * 60 * 60)

    #run_script("python/check_prediction.py")

    print(f"\n✅ Proceso finalizado a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Mostrar visualización si se desea
    if input("\n¿Deseas abrir el dashboard de visualización? (s/n): ").lower() == "s":
        os.system("streamlit run python/dashboard.py")

if __name__ == "__main__":
    main()