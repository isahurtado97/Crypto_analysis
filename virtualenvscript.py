import os
import sys
import venv

def create_virtual_environment():
    # Get the current directory
    current_dir = os.getcwd()
    
    # Get the folder name from the current directory path
    folder_name = os.path.basename(current_dir)
    
    # Define the path for the virtual environment
    venv_path = os.path.join(current_dir, folder_name)
    
    # Check if the virtual environment folder already exists
    if os.path.exists(venv_path):
        print(f"A virtual environment named '{folder_name}' already exists in this directory.")
        return
    
    try:
        # Create the virtual environment
        venv.create(venv_path, with_pip=True)
        print(f"Virtual environment '{folder_name}' has been successfully created.")
        print(f"Activate it using:\n  source {folder_name}/bin/activate (Linux/Mac)\n  {folder_name}\\Scripts\\activate (Windows)")
    except Exception as e:
        print(f"An error occurred while creating the virtual environment: {e}")

if __name__ == "__main__":
    create_virtual_environment()
#Activate venv source AI-Trading/bin/activate