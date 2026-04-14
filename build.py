import os
import subprocess
import sys

def main():
    print("Building Cygnus.exe with PyInstaller...")

    # Define paths
    icon_path = "src/app/assets/logo.ico"
    main_script = "src/app/main.py"
    
    # Define data files to bundle. Windows uses ';' as the separator for --add-data
    data_assets = "src/app/assets;app/assets"
    data_data = "src/app/data;app/data"

    # Construct the PyInstaller command
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",         # Overwrite output directory if it exists
        "--onefile",           # One-file bundled executable
        "--windowed",          # Prevent opening a console window
        f"--name=Cygnus",      # Name of the output executable
        f"--icon={icon_path}", # App icon
        f"--add-data={data_assets}", # Bundle assets
        f"--add-data={data_data}",   # Bundle data (quotes.json, etc.)
        "--paths=src",               # Help PyInstaller find the imported 'app' module
        "--hidden-import=sqlmodel",  # Ensure sqlmodel is bundled
        "--hidden-import=pydantic",  # Ensure pydantic is bundled
        "--hidden-import=sqlalchemy",# Ensure sqlalchemy is bundled
        # Hide output from unneeded PyInstaller imports/logs to keep console clean, but leave standard output.
        "--log-level=WARN",
        main_script            # Entry point
    ]

    try:
        # Run the command using subprocess
        result = subprocess.run(command, check=True, text=True)
        print("\nBuild Successful! The executable is located in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild Failed with error code {e.returncode}.")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("\nPyInstaller not found. Ensure you are running this in the uv environment (e.g., `uv run python build.py`).")
        sys.exit(1)

if __name__ == "__main__":
    main()
