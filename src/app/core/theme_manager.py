# src/app/core/theme_manager.py
import os
import re
from pathlib import Path
from PySide6.QtWidgets import QApplication
from app.data.settings_store import load_setting, save_setting

THEMES = {
    "Fox (Amber)": {
        "bg": "#1E1F22",
        "bg_sec": "#2A2C31",
        "accent": "#FFB347",
        "hover": "#FFC66D",
        "text": "#F5F1E8",
        "muted": "#A8A29E",
        "border": "#3F4147",
    },
    "Wolf (Blue)": {
        "bg": "#181A1F",
        "bg_sec": "#21252B",
        "accent": "#528BFF",
        "hover": "#73A5FF",
        "text": "#ABB2BF",
        "muted": "#5C6370",
        "border": "#3E4451",
    },
    "Panther (Purple)": {
        "bg": "#0D0D14",
        "bg_sec": "#161622",
        "accent": "#9D4EDD",
        "hover": "#C77DFF",
        "text": "#E0E1DD",
        "muted": "#778DA9",
        "border": "#2E2E3A",
    },
    "Peacock (Teal)": {
        "bg": "#0B1D28",
        "bg_sec": "#112B3C",
        "accent": "#20B2AA",
        "hover": "#48D1CC",
        "text": "#E0F7FA",
        "muted": "#80DEEA",
        "border": "#26547C",
    },
    "Flamingo (Rose)": {
        "bg": "#2D1B2E",
        "bg_sec": "#3E2740",
        "accent": "#FF758F",
        "hover": "#FF8FA3",
        "text": "#FFD6E0",
        "muted": "#CBAACD",
        "border": "#5A3A5E",
    },
    "Serpent (Emerald)": {
        "bg": "#0F1A15",
        "bg_sec": "#182820",
        "accent": "#10B981",
        "hover": "#34D399",
        "text": "#ECFDF5",
        "muted": "#6EE7B7",
        "border": "#065F46",
    }
}

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def apply_theme(theme_name: str, app_root: Path):
    if theme_name not in THEMES:
        return

    new_colors = THEMES[theme_name]
    qss_path = app_root / "assets" / "theme.qss"
    old_theme_name = None
    
    if qss_path.exists():
        try:
            qss_content = qss_path.read_text(encoding="utf-8")
            # Search for QMainWindow background color
            match = re.search(r'QMainWindow\s*\{\s*background-color:\s*(#[0-9a-fA-F]+);', qss_content)
            if match:
                detected_bg = match.group(1).upper()
                for name, colors in THEMES.items():
                    if colors["bg"].upper() == detected_bg:
                        old_theme_name = name
                        break
        except Exception as e:
            print(f"Error auto-detecting theme: {e}")

    if not old_theme_name:
        old_theme_name = load_setting("current_theme", "Fox (Amber)")
        if old_theme_name not in THEMES:
            old_theme_name = "Fox (Amber)"
        
    old_colors = THEMES[old_theme_name]

    if old_theme_name == theme_name:
        # Save anyway just in case the JSON was out of sync
        save_setting("current_theme", theme_name)
        return

    replacements = {
        old_colors["bg"]: new_colors["bg"],
        old_colors["bg_sec"]: new_colors["bg_sec"],
        old_colors["accent"]: new_colors["accent"],
        old_colors["hover"]: new_colors["hover"],
        old_colors["text"]: new_colors["text"],
        old_colors["muted"]: new_colors["muted"],
        old_colors["border"]: new_colors["border"],
    }
    
    old_r, old_g, old_b = hex_to_rgb(old_colors["accent"])
    new_r, new_g, new_b = hex_to_rgb(new_colors["accent"])
    
    rgba_replacements = {
        f"rgba\\(\\s*{old_r}\\s*,\\s*{old_g}\\s*,\\s*{old_b}\\s*,": f"rgba({new_r}, {new_g}, {new_b},",
    }

    # Iterate over all .qss and .py files in app directory
    for root, _, files in os.walk(app_root):
        # Prevent self-modification
        if 'theme_manager.py' in root or 'theme_manager.py' in files:
            files = [f for f in files if f != 'theme_manager.py']

        for file in files:
            if file.endswith('.py') or file.endswith('.qss'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    changed = False
                    for old, new in replacements.items():
                        # Use positive lookahead/behind to avoid replacing partial hex
                        # e.g. don't replace #FFFFFF if looking for #FFF
                        if re.search(old, content, flags=re.IGNORECASE):
                            content = re.sub(old, new, content, flags=re.IGNORECASE)
                            changed = True
                            
                    for old, new in rgba_replacements.items():
                        if re.search(old, content, flags=re.IGNORECASE):
                            content = re.sub(old, new, content, flags=re.IGNORECASE)
                            changed = True
                            
                    if changed:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    save_setting("current_theme", theme_name)
    
    # Reload stylesheet
    qss_path = app_root / "assets" / "theme.qss"
    app = QApplication.instance()
    if app and qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
