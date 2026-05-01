# Cygnus 🦢

> A powerful, Yeolpumta-inspired study timer and productivity tracking application with rich analytics, built in Python and PyQt6.

## 📥 Download

The easiest way to use Cygnus on Windows is to download the **official installer**. This will install the app to your computer, create shortcuts, and enable **automatic updates**.

🚀 **[Download the Latest Windows Installer (Cygnus_Setup.exe)](https://github.com/MSameer404/Cygnus/releases/latest/download/Cygnus_Setup.exe)**

Alternatively, visit the [Releases page](https://github.com/MSameer404/Cygnus/releases) to see all available versions.

---

## ✨ Features

- **⏱️ Study Timer & Session Tracking**: Focus deeply with a Yeolpumta-inspired interface. Also supports the manual addition of past study sessions.
- **🔄 Auto-Update**: Never miss a feature! The app automatically checks for and installs new versions directly from GitHub.
- **📝 To-Do List Management**: Organize your tasks with an intuitive to-do list, complete with a comprehensive Weekly View.
- **📊 Rich Analytics & Heatmap**: Track your progress over time through detailed study heatmaps and analytics. 
- **📸 Daily Statistics Snapshot**: Generate, view, and share/download a beautiful daily snapshot of your study statistics.
- **👤 User Profile System**: Customize your experience with a personal user profile, including support for custom square profile pictures.
- **💡 Motivational Quotes**: Stay inspired with a curated collection of physics, math, and study-related motivational quotes displayed on the home page.
- **🛡️ Safe & Reliable**: Confirmation dialogs for destructive actions prevent accidental data loss.
- **📞 Contact Us**: Easily reach the developer via the integrated sidebar section for Reddit, Discord, and GitHub links.

## 🛠️ Technology Stack

- **[Python](https://www.python.org/)** (>= 3.13)
- **[PyQt6](https://riverbankcomputing.com/software/pyqt/)** - Modern GUI framework.
- **[SQLModel](https://sqlmodel.tiangolo.com/)** - Powerful database interaction combining SQL with Pydantic type hints.
- **[PyInstaller](https://pyinstaller.org/)** - For packaging the app into a standalone Windows `.exe`.
- **[uv](https://github.com/astral-sh/uv)** - For ultra-fast Python project and package management.

## 🚀 Running Locally & Development

### Prerequisites

Ensure you have [Python 3.13+](https://www.python.org/downloads/) installed. We recommend using `uv` for managing dependencies.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MSameer404/Cygnus.git
   cd Cygnus
   ```

2. **Install dependencies:**
   Using `uv` (recommended):
   ```bash
   uv sync
   ```
   Or using `pip`:
   ```bash
   pip install .
   ```
   *(If you are installing for development, you can use `uv sync --group dev`)*

### Running the App

To start Cygnus from the source, run:

```bash
uv run src/app/main.py
```

### Packaging the Application for Windows (EXE + Installer)

To create a professional release:

1. **Build the Executable**:
   ```bash
   uv run python build.py
   ```
   *This creates `Cygnus.exe` in the `dist` folder.*

2. **Build the Installer**:
   - Open `setup.iss` in **Inno Setup**.
   - Click **Compile**.
   - Your final installer `Cygnus_Setup.exe` will be ready in the `dist` folder.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check out the [issues page](https://github.com/MSameer404/Cygnus/issues) if you want to contribute.

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
