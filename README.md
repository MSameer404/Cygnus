# Cygnus 🦢

> A powerful, Yeolpumta-inspired study timer and productivity tracking application with rich analytics, built in Python and PySide6.



## ✨ Features

- **⏱️ Study Timer & Session Tracking**: Focus deeply with a Yeolpumta-inspired interface. Also supports the manual addition of past study sessions.
- **🔄 Update Alerts**: Never miss a feature! The app automatically checks for new versions directly from GitHub and notifies you when an update is available.
- **📝 To-Do List Management**: Organize your tasks with an intuitive to-do list, complete with a comprehensive Weekly View.
- **📊 Rich Analytics & Heatmap**: Track your progress over time through detailed study heatmaps and analytics. 
- **📸 Daily Statistics Snapshot**: Generate, view, and share/download a beautiful daily snapshot of your study statistics.
- **👤 User Profile System**: Customize your experience with a personal user profile, including support for custom square profile pictures.
- **💡 Motivational Quotes**: Stay inspired with a curated collection of physics, math, and study-related motivational quotes displayed on the home page.
- **🛡️ Safe & Reliable**: Confirmation dialogs for destructive actions prevent accidental data loss.
- **📞 Contact Us**: Easily reach the developer via the integrated sidebar section for Reddit, Discord, and GitHub links.

## 🛠️ Technology Stack

- **[Python](https://www.python.org/)** (>= 3.13)
- **[PySide6](https://doc.qt.io/qtforpython-6/)** - Modern GUI framework (LGPL licensed).
- **[SQLModel](https://sqlmodel.tiangolo.com/)** - Powerful database interaction combining SQL with Pydantic type hints.
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


## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check out the [issues page](https://github.com/MSameer404/Cygnus/issues) if you want to contribute.

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
