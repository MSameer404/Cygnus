# src/app/ui/widgets/html_report_generator.py
"""Generate beautiful HTML report card for study statistics."""

import json
import random
import webbrowser
from datetime import date, datetime
from pathlib import Path

from app.core import dday_manager, profile_manager, session_manager, stats_engine
from app.core.timer_engine import TimerEngine


def format_total_time_html(seconds: int) -> str:
    """Format total time with big numbers and small text for top display."""
    if seconds == 0:
        return '<span class="time-num">0</span><span class="time-unit">hr</span> <span class="time-num">0</span><span class="time-unit">min</span> <span class="time-num">0</span><span class="time-unit">sec</span>'
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if hours > 0:
        parts.append(f'<span class="time-num">{hours}</span><span class="time-unit">hr</span>')
    if minutes > 0 or (hours > 0 and secs == 0):
        parts.append(f'<span class="time-num">{minutes}</span><span class="time-unit">min</span>')
    if secs > 0 or (hours == 0 and minutes == 0):
        parts.append(f'<span class="time-num">{secs}</span><span class="time-unit">sec</span>')
    return " ".join(parts)


def format_time_simple_html(seconds: int) -> str:
    """Format time with big numbers and small units for subjects and sessions."""
    if seconds == 0:
        return '<span class="small-num">0</span><span class="small-unit">hr</span> <span class="small-num">0</span><span class="small-unit">min</span>'
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if hours > 0:
        parts.append(f'<span class="small-num">{hours}</span><span class="small-unit">hr</span>')
    if minutes > 0 or hours == 0:
        parts.append(f'<span class="small-num">{minutes}</span><span class="small-unit">min</span>')
    return " ".join(parts)


def get_random_quote() -> dict:
    """Load and return a random quote from quotes.json."""
    quotes_path = Path(__file__).parent.parent.parent / "data" / "quotes.json"
    try:
        with open(quotes_path, "r", encoding="utf-8") as f:
            quotes = json.load(f)
        return random.choice(quotes) if quotes else {"text": "Stay focused and keep learning!", "author": "Cygnus"}
    except Exception:
        return {"text": "Stay focused and keep learning!", "author": "Cygnus"}


def generate_html_report(target_date: date, output_path: Path | None = None) -> Path:
    """Generate an HTML report for the given date and save to file."""
    
    # Gather all data
    profile = profile_manager.get_profile()
    total_seconds = stats_engine.get_daily_total(target_date)
    streak = stats_engine.get_streak()
    subject_breakdown = stats_engine.get_subject_breakdown(target_date, target_date)
    sessions = session_manager.get_sessions_for_date(target_date)
    quote = get_random_quote()
    
    # Get upcoming D-Day events
    upcoming_events = dday_manager.list_upcoming_events()
    days_until_exam = None
    exam_name = None
    if upcoming_events:
        next_event = upcoming_events[0]
        days_until_exam = (next_event.target_date - date.today()).days
        exam_name = next_event.title
    
    # Profile data (name and class/grade only)
    name = profile.get("name") or "Cygnus Student"
    p_class = profile.get("class") or ""
    
    # Session stats
    session_count = len(sessions)
    avg_session = total_seconds // session_count if session_count > 0 else 0
    longest_session = max((s.duration_seconds for s in sessions), default=0)
    
    # Format times
    total_formatted = format_total_time_html(total_seconds)
    avg_formatted = format_time_simple_html(avg_session)
    longest_formatted = format_time_simple_html(longest_session) if longest_session > 0 else "—"
    
    # Date formatting
    date_str = target_date.strftime("%A, %B %d, %Y")
    
    # Build pie chart segments
    pie_segments = []
    pie_legend = []
    colors = ["#6C5CE7", "#00CEC9", "#FF6B6B", "#FDCB6E", "#A29BFE", "#74B9FF", "#55EFC4"]
    
    if subject_breakdown:
        total_subj_time = sum(item.get("seconds", 0) if isinstance(item, dict) else 0 for item in subject_breakdown.values())
        if total_subj_time == 0:
            total_subj_time = 1  # Avoid division by zero
        
        cumulative = 0
        for idx, (subj_name, item) in enumerate(subject_breakdown.items()):
            if isinstance(item, dict):
                color = item.get("color_hex", colors[idx % len(colors)])
                seconds = item.get("seconds", 0)
            else:
                color = colors[idx % len(colors)]
                seconds = 0
            
            if seconds > 0:
                percentage = (seconds / total_subj_time) * 100
                angle = (seconds / total_subj_time) * 360
                
                # SVG pie segment
                pie_segments.append(f'<div class="pie-segment" style="--percentage: {percentage:.1f}; --color: {color}; --index: {idx};"></div>')
                
                # Legend item with styled time format
                time_str = format_time_simple_html(seconds)
                pie_legend.append(f'''
                    <div class="legend-item">
                        <div class="legend-dot" style="background: {color};"></div>
                        <span class="legend-name">{subj_name}</span>
                        <span class="legend-value">{time_str}</span>
                    </div>
                ''')
    
    # Profile picture handling (base64 if exists)
    pfp_html = ""
    pfp_path = profile_manager.get_profile_picture_path()
    if pfp_path and pfp_path.exists():
        import base64
        try:
            with open(pfp_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            pfp_html = f'<img src="data:image/png;base64,{img_data}" alt="Profile" class="profile-img">'
        except Exception:
            pfp_html = '<div class="profile-img-placeholder">📖</div>'
    else:
        pfp_html = '<div class="profile-img-placeholder">📖</div>'
    
    # Build streak HTML with fire emoji
    streak_html = f"""
        <div class="streak-number">🔥 {streak}</div>
        <div class="streak-label">day{'s' if streak != 1 else ''} streak</div>
    """
    
    # Days until exam HTML
    dday_html = ""
    if days_until_exam is not None and exam_name:
        dday_html = f'<div class="dday-text">{exam_name} in <span class="dday-number">{days_until_exam}</span> days</div>'
    else:
        dday_html = '<div class="dday-text">No upcoming exams</div>'
    
    # HTML Template
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cygnus Study Report - {date_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1E1E2E 0%, #252535 100%);
            color: #EAEAF0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        
        .report-card {{
            width: 100%;
            max-width: 1200px;
            background: rgba(37, 37, 53, 0.8);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        /* Top Row */
        .top-row {{
            display: grid;
            grid-template-columns: 280px 1fr 200px;
            gap: 24px;
            margin-bottom: 30px;
        }}
        
        /* Profile Card */
        .profile-card {{
            background: rgba(30, 30, 46, 0.6);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .profile-img, .profile-img-placeholder {{
            width: 64px;
            height: 64px;
            border-radius: 50%;
            object-fit: cover;
            background: linear-gradient(135deg, #6C5CE7, #00CEC9);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
        }}
        
        .profile-info {{
            flex: 1;
        }}
        
        .profile-name {{
            font-size: 20px;
            font-weight: 700;
            color: #EAEAF0;
            margin-bottom: 4px;
        }}
        
        .profile-details {{
            font-size: 13px;
            color: #8B8BA0;
        }}
        
        /* Center Card */
        .center-card {{
            background: linear-gradient(135deg, rgba(108, 92, 231, 0.2), rgba(0, 206, 201, 0.1));
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            border: 1px solid rgba(108, 92, 231, 0.3);
            box-shadow: 0 4px 20px rgba(108, 92, 231, 0.15);
        }}
        
        .date-label {{
            font-size: 18px;
            font-weight: 700;
            color: #6C5CE7;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }}
        
        .total-time {{
            font-size: 20px;
            font-weight: 600;
            color: #EAEAF0;
            text-shadow: 0 2px 10px rgba(108, 92, 231, 0.5);
            margin-bottom: 12px;
            letter-spacing: 0;
            line-height: 1.4;
        }}
        
        .time-num {{
            font-size: 48px;
            font-weight: 800;
            color: #fff;
            margin: 0 2px;
        }}
        
        .time-unit {{
            font-size: 16px;
            font-weight: 500;
            color: #A29BFE;
            margin-right: 8px;
        }}
        
        /* Small number styling for subjects and sessions */
        .small-num {{
            font-size: 24px;
            font-weight: 800;
            color: inherit;
        }}
        
        .small-unit {{
            font-size: 12px;
            font-weight: 500;
            color: #8B8BA0;
            margin-right: 6px;
        }}
        
        .dday-text {{
            font-size: 14px;
            color: #A29BFE;
        }}
        
        .dday-number {{
            font-weight: 700;
            color: #FDCB6E;
        }}
        
        /* Streak Card */
        .streak-card {{
            background: rgba(30, 30, 46, 0.6);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        
        .streak-number {{
            font-size: 42px;
            font-weight: 800;
            color: #FF6B6B;
            line-height: 1;
        }}
        
        .streak-label {{
            font-size: 14px;
            color: #8B8BA0;
            margin-top: 4px;
        }}
        
        /* Bottom Row */
        .bottom-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }}
        
        /* Section Cards */
        .section-card {{
            background: rgba(30, 30, 46, 0.6);
            border-radius: 16px;
            padding: 28px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            color: #A29BFE;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Pie Chart */
        .pie-container {{
            display: flex;
            align-items: center;
            gap: 30px;
        }}
        
        .pie-chart {{
            width: 160px;
            height: 160px;
            border-radius: 50%;
            background: conic-gradient(
                {', '.join([f"{colors[i % len(colors)]} {sum(list(subject_breakdown.values())[j].get('seconds', 0) if isinstance(list(subject_breakdown.values())[j], dict) else 0 for j in range(i)) / max(sum(item.get('seconds', 0) if isinstance(item, dict) else 0 for item in subject_breakdown.values()), 1) * 360}deg {sum(list(subject_breakdown.values())[j].get('seconds', 0) if isinstance(list(subject_breakdown.values())[j], dict) else 0 for j in range(i + 1)) / max(sum(item.get('seconds', 0) if isinstance(item, dict) else 0 for item in subject_breakdown.values()), 1) * 360}deg" for i in range(len(subject_breakdown))]) if subject_breakdown else "#3D3D4A 0deg 360deg"}
            );
            position: relative;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}
        
        .pie-center {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80px;
            height: 80px;
            background: #252535;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            color: #8B8BA0;
            text-align: center;
        }}
        
        .legend {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        .legend-name {{
            flex: 1;
            font-size: 14px;
            color: #EAEAF0;
        }}
        
        .legend-value {{
            font-size: 24px;
            font-weight: 800;
            color: #EAEAF0;
        }}
        
        /* Stats */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        .stat-item {{
            text-align: center;
            background: rgba(30, 30, 46, 0.4);
            border-radius: 12px;
            padding: 16px 8px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: 800;
            color: #00CEC9;
            line-height: 1.3;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: #8B8BA0;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Quote */
        .quote-box {{
            background: rgba(26, 26, 36, 0.8);
            border-left: 3px solid #6C5CE7;
            border-radius: 8px;
            padding: 16px;
            margin-top: auto;
        }}
        
        .quote-text {{
            font-size: 14px;
            color: #A6ACCD;
            font-style: italic;
            line-height: 1.5;
            margin-bottom: 8px;
        }}
        
        .quote-author {{
            font-size: 12px;
            color: #6B6B7B;
            text-align: right;
        }}
        
        /* Footer */
        .footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .footer-text {{
            font-size: 13px;
            color: #6B6B7B;
        }}
        
        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #6B6B7B;
        }}
        
        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}
    </style>
</head>
<body>
    <div class="report-card">
        <!-- Top Row -->
        <div class="top-row">
            <!-- Profile Card -->
            <div class="profile-card">
                {pfp_html}
                <div class="profile-info">
                    <div class="profile-name">{name}</div>
                    <div class="profile-details">{p_class}</div>
                </div>
            </div>
            
            <!-- Center Card: Date & Total Time -->
            <div class="center-card">
                <div class="date-label">{date_str}</div>
                <div class="total-time">{total_formatted}</div>
                {dday_html}
            </div>
            
            <!-- Streak Card -->
            <div class="streak-card">
                {streak_html}
            </div>
        </div>
        
        <!-- Bottom Row -->
        <div class="bottom-row">
            <!-- Subject Breakdown -->
            <div class="section-card">
                <div class="section-title">Subject Breakdown</div>
                {"<div class='pie-container'><div class=\"pie-chart\"><div class=\"pie-center\">Study<br>Time</div></div><div class=\"legend\">" + "".join(pie_legend) + "</div></div>" if pie_legend else "<div class='empty-state'><div class='empty-state-icon'>📊</div>No subjects tracked today</div>"}
            </div>
            
            <!-- Session Statistics -->
            <div class="section-card">
                <div class="section-title">Session Statistics</div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{session_count}</div>
                        <div class="stat-label">Sessions</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{avg_formatted}</div>
                        <div class="stat-label">Avg Session</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{longest_formatted}</div>
                        <div class="stat-label">Longest</div>
                    </div>
                </div>
                <div class="quote-box">
                    <div class="quote-text">"{quote.get("text", "")}"</div>
                    <div class="quote-author">— {quote.get("author", "Unknown")}</div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer" style="justify-content: center;">
            <div class="footer-text">Made by Cygnus</div>
        </div>
    </div>
</body>
</html>
'''
    
    # Save to file
    if output_path is None:
        output_path = Path.home() / f"Cygnus_Report_{target_date.strftime('%Y-%m-%d')}.html"
    
    output_path.write_text(html, encoding="utf-8")
    return output_path


def generate_week_html_report(week_start: date, output_path: Path | None = None) -> Path:
    """Generate an HTML report for the week and save to file."""
    from datetime import timedelta
    
    week_end = week_start + timedelta(days=6)
    quote = get_random_quote()
    
    # Gather data
    profile = profile_manager.get_profile()
    name = profile.get("name") or "Cygnus Student"
    p_class = profile.get("class") or ""
    
    # Weekly totals and daily data
    daily_totals = stats_engine.get_weekly_totals(week_start)
    total_seconds = sum(daily_totals)
    subject_breakdown = stats_engine.get_subject_breakdown(week_start, week_end)
    
    # Get all sessions for the week to calculate best session and average session
    all_sessions = []
    for day_offset in range(7):
        day = week_start + timedelta(days=day_offset)
        all_sessions.extend(session_manager.get_sessions_for_date(day))
    
    # Calculate stats
    session_count = len(all_sessions)
    avg_daily_seconds = total_seconds // 7  # Average per day of week
    avg_session_seconds = total_seconds // session_count if session_count > 0 else 0
    
    # Find best day (day with most study time)
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    best_day_idx = daily_totals.index(max(daily_totals)) if daily_totals and max(daily_totals) > 0 else -1
    best_day_name = day_labels[best_day_idx] if best_day_idx >= 0 else "—"
    best_day_seconds = daily_totals[best_day_idx] if best_day_idx >= 0 else 0
    
    # Format stats for display
    avg_daily_formatted = format_time_simple_html(avg_daily_seconds)
    best_day_time_formatted = format_time_simple_html(best_day_seconds)
    avg_session_formatted = format_time_simple_html(avg_session_seconds)
    
    # Profile picture
    pfp_html = ""
    pfp_path = profile_manager.get_profile_picture_path()
    if pfp_path and pfp_path.exists():
        import base64
        try:
            with open(pfp_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            pfp_html = f'<img src="data:image/png;base64,{img_data}" alt="Profile" class="profile-img">'
        except Exception:
            pfp_html = '<div class="profile-img-placeholder">📖</div>'
    else:
        pfp_html = '<div class="profile-img-placeholder">📖</div>'
    
    # Week date range
    week_str = f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}"
    
    # Total time with styled numbers
    total_formatted = format_total_time_html(total_seconds)
    
    # Build subject breakdown legend
    pie_legend = []
    colors = ["#6C5CE7", "#00CEC9", "#FF6B6B", "#FDCB6E", "#A29BFE", "#74B9FF", "#55EFC4"]
    
    if subject_breakdown:
        for idx, (subj_name, item) in enumerate(subject_breakdown.items()):
            if isinstance(item, dict):
                color = item.get("color_hex", colors[idx % len(colors)])
                seconds = item.get("seconds", 0)
            else:
                color = colors[idx % len(colors)]
                seconds = 0
            
            if seconds > 0:
                time_str = format_time_simple_html(seconds)
                pie_legend.append(f'''
                    <div class="legend-item">
                        <div class="legend-dot" style="background: {color};"></div>
                        <span class="legend-name">{subj_name}</span>
                        <span class="legend-value">{time_str}</span>
                    </div>
                ''')
    
    # Build daily bar chart (CSS)
    max_total = max(daily_totals) if daily_totals else 1
    if max_total == 0:
        max_total = 1
    
    bar_html = '<div class="week-bars">'
    for i, (day_label, seconds) in enumerate(zip(day_labels, daily_totals)):
        height_pct = (seconds / max_total) * 100 if max_total > 0 else 0
        time_str = format_time_simple_html(seconds)
        bar_html += f'''
            <div class="bar-wrapper">
                <div class="bar" style="height: {max(height_pct, 5)}%;">
                    <span class="bar-value">{time_str}</span>
                </div>
                <div class="bar-label">{day_label}</div>
            </div>
        '''
    bar_html += '</div>'
    
    # HTML Template
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cygnus Week Report - {week_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1E1E2E 0%, #252535 100%);
            color: #EAEAF0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        
        .report-card {{
            width: 100%;
            max-width: 1200px;
            background: rgba(37, 37, 53, 0.8);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        /* Top Row */
        .top-row {{
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 24px;
            margin-bottom: 30px;
        }}
        
        /* Profile Card */
        .profile-card {{
            background: rgba(30, 30, 46, 0.6);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .profile-img, .profile-img-placeholder {{
            width: 64px;
            height: 64px;
            border-radius: 50%;
            object-fit: cover;
            background: linear-gradient(135deg, #6C5CE7, #00CEC9);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
        }}
        
        .profile-info {{
            flex: 1;
        }}
        
        .profile-name {{
            font-size: 20px;
            font-weight: 700;
            color: #EAEAF0;
            margin-bottom: 4px;
        }}
        
        .profile-details {{
            font-size: 13px;
            color: #8B8BA0;
        }}
        
        /* Week Card */
        .week-card {{
            background: linear-gradient(135deg, rgba(108, 92, 231, 0.2), rgba(0, 206, 201, 0.1));
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            border: 1px solid rgba(108, 92, 231, 0.3);
            box-shadow: 0 4px 20px rgba(108, 92, 231, 0.15);
        }}
        
        .week-label {{
            font-size: 18px;
            font-weight: 700;
            color: #6C5CE7;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }}
        
        .total-time {{
            font-size: 20px;
            font-weight: 600;
            color: #EAEAF0;
            text-shadow: 0 2px 10px rgba(108, 92, 231, 0.5);
            line-height: 1.4;
        }}
        
        .time-num {{
            font-size: 48px;
            font-weight: 800;
            color: #fff;
            margin: 0 2px;
        }}
        
        .time-unit {{
            font-size: 16px;
            font-weight: 500;
            color: #A29BFE;
            margin-right: 8px;
        }}
        
        /* Small number styling for subjects */
        .small-num {{
            font-size: 24px;
            font-weight: 800;
            color: inherit;
        }}
        
        .small-unit {{
            font-size: 12px;
            font-weight: 500;
            color: #8B8BA0;
            margin-right: 6px;
        }}
        
        /* Middle Row */
        .middle-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }}
        
        /* Section Cards */
        .section-card {{
            background: rgba(30, 30, 46, 0.6);
            border-radius: 16px;
            padding: 28px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            color: #A29BFE;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Subject Legend */
        .legend {{
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        
        .legend-name {{
            flex: 1;
            font-size: 15px;
            color: #EAEAF0;
        }}
        
        .legend-value {{
            font-size: 24px;
            font-weight: 800;
            color: #EAEAF0;
        }}
        
        /* Week Bar Chart */
        .week-bars {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            height: 200px;
            gap: 12px;
            padding: 10px 0;
        }}
        
        .bar-wrapper {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }}
        
        .bar {{
            width: 100%;
            max-width: 60px;
            background: linear-gradient(to top, #6C5CE7, #00CEC9);
            border-radius: 8px 8px 4px 4px;
            position: relative;
            min-height: 5px;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding-top: 8px;
        }}
        
        .bar-value {{
            font-size: 11px;
            font-weight: 700;
            color: #1E1E2E;
            text-align: center;
            line-height: 1.2;
            background: rgba(255, 255, 255, 0.85);
            padding: 2px 4px;
            border-radius: 4px;
            backdrop-filter: blur(2px);
        }}
        
        .bar-label {{
            font-size: 12px;
            font-weight: 600;
            color: #8B8BA0;
            text-transform: uppercase;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin: 24px 0;
        }}
        
        .stat-item {{
            text-align: center;
            background: rgba(30, 30, 46, 0.6);
            border-radius: 12px;
            padding: 20px 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .stat-value {{
            font-size: 22px;
            font-weight: 800;
            color: #00CEC9;
            line-height: 1.3;
            margin-bottom: 6px;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: #8B8BA0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Quote Box */
        .quote-box {{
            background: rgba(26, 26, 36, 0.8);
            border-left: 3px solid #6C5CE7;
            border-radius: 8px;
            padding: 20px;
        }}
        
        .quote-text {{
            font-size: 15px;
            color: #A6ACCD;
            font-style: italic;
            line-height: 1.5;
            margin-bottom: 10px;
        }}
        
        .quote-author {{
            font-size: 13px;
            color: #6B6B7B;
            text-align: right;
        }}
        
        /* Footer */
        .footer {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .footer-text {{
            font-size: 13px;
            color: #6B6B7B;
        }}
        
        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #6B6B7B;
        }}
        
        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}
    </style>
</head>
<body>
    <div class="report-card">
        <!-- Top Row -->
        <div class="top-row">
            <!-- Profile Card -->
            <div class="profile-card">
                {pfp_html}
                <div class="profile-info">
                    <div class="profile-name">{name}</div>
                    <div class="profile-details">{p_class}</div>
                </div>
            </div>
            
            <!-- Week Card -->
            <div class="week-card">
                <div class="week-label">{week_str}</div>
                <div class="total-time">{total_formatted}</div>
            </div>
        </div>
        
        <!-- Middle Row -->
        <div class="middle-row">
            <!-- Subject Breakdown -->
            <div class="section-card">
                <div class="section-title">Subject Breakdown</div>
                {"<div class=\"legend\">" + "".join(pie_legend) + "</div>" if pie_legend else "<div class='empty-state'><div class='empty-state-icon'>📊</div>No subjects tracked this week</div>"}
            </div>
            
            <!-- Daily Study Time -->
            <div class="section-card">
                <div class="section-title">Daily Study Time</div>
                {bar_html if any(daily_totals) else "<div class='empty-state'><div class='empty-state-icon'>📈</div>No study sessions this week</div>"}
            </div>
        </div>
        
        <!-- Week Statistics -->
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">{avg_daily_formatted}</div>
                <div class="stat-label">Avg Daily</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{best_day_time_formatted}</div>
                <div class="stat-label">Best Day ({best_day_name})</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{avg_session_formatted}</div>
                <div class="stat-label">Avg Session</div>
            </div>
        </div>
        
        <!-- Quote -->
        <div class="quote-box">
            <div class="quote-text">"{quote.get("text", "")}"</div>
            <div class="quote-author">— {quote.get("author", "Unknown")}</div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div class="footer-text">Made by Cygnus</div>
        </div>
    </div>
</body>
</html>
'''
    
    # Save to file
    if output_path is None:
        output_path = Path.home() / f"Cygnus_Week_Report_{week_start.strftime('%Y-%m-%d')}.html"
    
    output_path.write_text(html, encoding="utf-8")
    return output_path


def open_report_in_browser(html_path: Path) -> None:
    """Open the HTML report in the default browser."""
    webbrowser.open(f"file://{html_path.resolve()}")
