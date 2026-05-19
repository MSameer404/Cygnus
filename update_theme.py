import os
import re

replacements = {
    "#0F0F14": "#1E1F22",
    "#1A1A28": "#2A2C31",
    "#141420": "#2A2C31",
    "#1E1E30": "#2A2C31",
    "#1A0A2E": "#2A2C31",
    "#14102A": "#2A2C31",
    "#0D0A20": "#2A2C31",
    "#0D1A2E": "#2A2C31",
    "#22203A": "#2A2C31",
    "#1E1E32": "#2A2C31",
    "#2A2A42": "#2A2C31",
    "#252535": "#2A2C31",
    "#2D2D45": "#3F4147",
    "#3D3D60": "#3F4147",
    "#2D1B69": "#3F4147",
    "#3A3A55": "#3F4147",
    "#4C3D8A": "#3F4147",
    "#2D2D50": "#3F4147",
    "#EAEAF0": "#F5F1E8",
    "#FFFFFF": "#F5F1E8",
    "#8B8BA0": "#A8A29E",
    "#7B6FAA": "#A8A29E",
    "#7C3AED": "#FFB347",
    "#06B6D4": "#FFB347",
    "#10B981": "#FFB347",
    "#F43F5E": "#FFB347",
    "#F59E0B": "#FFB347",
    "#EC4899": "#FFB347",
    "#A78BFA": "#FFB347",
    "#C4B5FD": "#FFB347",
    "#8B5CF6": "#FFC66D",
    "#6D28D9": "#FFC66D",
    "#5B21B6": "#FFC66D",
    "#0891B2": "#FFC66D",
    "#22D3EE": "#FFC66D",
    "#E11D48": "#FFC66D",
    "#FB7185": "#FFC66D",
    "#059669": "#FFC66D",
    "#34D399": "#FFC66D",
    "#047857": "#FFC66D",
}

rgba_replacements = {
    # 124, 58, 237 (#7C3AED) -> 255, 179, 71
    r"rgba\(\s*124\s*,\s*58\s*,\s*237\s*,": "rgba(255, 179, 71,",
    # 6, 182, 212 (#06B6D4) -> 255, 179, 71
    r"rgba\(\s*6\s*,\s*182\s*,\s*212\s*,": "rgba(255, 179, 71,",
    # 244, 63, 94 (#F43F5E) -> 255, 179, 71
    r"rgba\(\s*244\s*,\s*63\s*,\s*94\s*,": "rgba(255, 179, 71,",
    # 30, 30, 48 -> 42, 44, 49
    r"rgba\(\s*30\s*,\s*30\s*,\s*48\s*,": "rgba(42, 44, 49,",
}

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Apply hex replacements (case insensitive match for hex)
    for old, new in replacements.items():
        content = re.sub(old, new, content, flags=re.IGNORECASE)

    # Apply rgba replacements
    for old, new in rgba_replacements.items():
        content = re.sub(old, new, content, flags=re.IGNORECASE)

    with open(filepath, 'w') as f:
        f.write(content)

# Process theme.qss
process_file('/home/sameer/Projects/SaaS/Cygnus/src/app/assets/theme.qss')

# Process timer_page.py
process_file('/home/sameer/Projects/SaaS/Cygnus/src/app/ui/timer_page.py')

# Also search through all python files to make sure we catch everything
for root, _, files in os.walk('/home/sameer/Projects/SaaS/Cygnus/src/app/ui'):
    for file in files:
        if file.endswith('.py') and file != 'timer_page.py':
            process_file(os.path.join(root, file))

print("Theme updated successfully!")
