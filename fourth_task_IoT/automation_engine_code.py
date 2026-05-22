import random
import csv
import time
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches

TOTAL_READINGS   = 10
INTERVAL_SECONDS = 1

CSV_FILE      = "automation_log.csv"
TEXT_FILE     = "automation_report.txt"
ALERT_FILE    = "automation_alerts.txt"
GRAPH_FILE    = "automation_dashboard.png"

THRESHOLDS = {
    "temperature_high" : 30.0,   # °C  → Turn ON AC
    "temperature_low"  : 24.0,   # °C  → Turn ON Heater
    "humidity_high"    : 65.0,   # %   → Turn ON Dehumidifier
    "humidity_low"     : 45.0,   # %   → Turn ON Humidifier
    "light_low"        : 350.0,  # lux → Turn ON Indoor Lights
    "light_high"       : 700.0,  # lux → Close Blinds
}

_state = {
    "temperature" : 28.0,
    "humidity"    : 55.0,
    "light"       : 400.0,
    "motion_cool" : 0,
}

# HVAC state memory
ac_on = False

def simulate_temperature():
    if random.random() < 0.03:
        _state["temperature"] += random.choice([-2.0, 2.0])
    else:
        _state["temperature"] += random.uniform(-0.8, 0.8)
    _state["temperature"] = max(20.0, min(40.0, _state["temperature"]))
    return round(_state["temperature"], 2)

def simulate_humidity():
    temp_effect = (_state["temperature"] - 28) * -0.15
    if random.random() < 0.03:
        _state["humidity"] += random.choice([-8.0, 8.0])
    else:
        _state["humidity"] += random.uniform(-1.2, 1.2)
    _state["humidity"] += temp_effect
    _state["humidity"] = max(30.0, min(90.0, _state["humidity"]))
    return round(_state["humidity"], 2)

def simulate_light():
    if random.random() < 0.03:
        _state["light"] += random.choice([-200.0, 200.0])
    else:
        _state["light"] += random.uniform(-25.0, 25.0)
    _state["light"] = max(0.0, min(1000.0, _state["light"]))
    return round(_state["light"], 2)

def simulate_motion():
    if _state["motion_cool"] > 0:
        _state["motion_cool"] -= 1
        return 0
    detected = random.choices([0, 1], weights=[80, 20])[0]
    if detected:
        _state["motion_cool"] = random.randint(2, 5)
    return detected

def read_sensors():
    return {
        "timestamp"   : datetime.now().strftime("%H:%M:%S"),
        "temperature" : simulate_temperature(),
        "humidity"    : simulate_humidity(),
        "motion"      : simulate_motion(),
        "light"       : simulate_light(),
    }

# =========================================================
# AUTOMATION ENGINE
# =========================================================

def evaluate_rules(reading):
    """
    Evaluate all automation rules against one sensor reading.

    Returns a list of triggered alert dicts:
        { sensor, condition, value, threshold, action, severity }

    Severity levels:
        "CRITICAL"  → immediate danger / urgent action
        "WARNING"   → abnormal but not dangerous
        "INFO"      → informational action
    """

    alerts = []

    t = reading["temperature"]
    h = reading["humidity"]
    l = reading["light"]
    m = reading["motion"]

    # ── Temperature Rules ──────────────────────────────────
    global ac_on

    # Turn ON AC only once
    if t > THRESHOLDS["temperature_high"] and not ac_on:

        ac_on = True

        alerts.append({
            "sensor"    : "Temperature",
            "condition" : f"> {THRESHOLDS['temperature_high']} °C",
            "value"     : f"{t} °C",
            "threshold" : THRESHOLDS["temperature_high"],
            "action"    : "Turn ON Air Conditioner",
            "severity"  : "CRITICAL",
            "icon"      : "🔴",
        })

    # Turn OFF AC after cooling
    elif t < 28.0 and ac_on:

        ac_on = False

        alerts.append({
            "sensor"    : "Temperature",
            "condition" : "< 28.0 °C",
            "value"     : f"{t} °C",
            "threshold" : 28.0,
            "action"    : "Turn OFF Air Conditioner",
            "severity"  : "INFO",
            "icon"      : "❄️",
        })

    # Heater logic
    elif t < THRESHOLDS["temperature_low"]:

        alerts.append({
            "sensor"    : "Temperature",
            "condition" : f"< {THRESHOLDS['temperature_low']} °C",
            "value"     : f"{t} °C",
            "threshold" : THRESHOLDS["temperature_low"],
            "action"    : "Turn ON Heater",
            "severity"  : "WARNING",
            "icon"      : "🔵",
        })

    # ── Humidity Rules ─────────────────────────────────────
    if h > THRESHOLDS["humidity_high"]:
        alerts.append({
            "sensor"    : "Humidity",
            "condition" : f"> {THRESHOLDS['humidity_high']} %",
            "value"     : f"{h} %",
            "threshold" : THRESHOLDS["humidity_high"],
            "action"    : "Turn ON Dehumidifier",
            "severity"  : "WARNING",
            "icon"      : "💧",
        })

    elif h < THRESHOLDS["humidity_low"]:
        alerts.append({
            "sensor"    : "Humidity",
            "condition" : f"< {THRESHOLDS['humidity_low']} %",
            "value"     : f"{h} %",
            "threshold" : THRESHOLDS["humidity_low"],
            "action"    : "Turn ON Humidifier",
            "severity"  : "WARNING",
            "icon"      : "🏜️",
        })

    # ── Light Rules ────────────────────────────────────────
    if l < THRESHOLDS["light_low"]:
        alerts.append({
            "sensor"    : "Light",
            "condition" : f"< {THRESHOLDS['light_low']} lux",
            "value"     : f"{l} lux",
            "threshold" : THRESHOLDS["light_low"],
            "action"    : "Turn ON Indoor Lights",
            "severity"  : "INFO",
            "icon"      : "💡",
        })

    elif l > THRESHOLDS["light_high"]:
        alerts.append({
            "sensor"    : "Light",
            "condition" : f"> {THRESHOLDS['light_high']} lux",
            "value"     : f"{l} lux",
            "threshold" : THRESHOLDS["light_high"],
            "action"    : "Close Window Blinds",
            "severity"  : "INFO",
            "icon"      : "☀️",
        })

    # ── Motion Rule ────────────────────────────────────────
    if m == 1:
        alerts.append({
            "sensor"    : "Motion",
            "condition" : "== DETECTED",
            "value"     : "DETECTED",
            "threshold" : None,
            "action"    : "Activate Security Light & Notify",
            "severity"  : "CRITICAL",
            "icon"      : "🚨",
        })

    return alerts


def init_csv():
    with open(CSV_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "No.", "Timestamp",
            "Temperature (°C)", "Humidity (%)", "Motion", "Light (lux)",
            "Alerts Triggered", "Actions",
        ])

def log_csv(reading, number, alerts):
    alert_count  = len(alerts)
    actions_text = " | ".join(a["action"] for a in alerts) if alerts else "NORMAL"

    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            number,
            reading["timestamp"],
            reading["temperature"],
            reading["humidity"],
            "DETECTED" if reading["motion"] == 1 else "NO MOTION",
            reading["light"],
            alert_count,
            actions_text,
        ])

BOX_WIDTH = 60

def box_line(label, value, unit=""):
    value_str = f"{value} {unit}".strip()
    content   = f"  {label:<22}: {value_str}"
    return f"│{content:<{BOX_WIDTH}}│\n"

def init_text():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        f.write("\n")
        f.write(f"{'╔' + '═' * BOX_WIDTH + '╗'}\n")
        f.write(f"║{'IoT AUTOMATION LOGIC REPORT':^{BOX_WIDTH}}║\n")
        f.write(f"║{'Decodelabs IoT Internship - Task 4':^{BOX_WIDTH}}║\n")
        f.write(f"║{('Generated: ' + now):^{BOX_WIDTH}}║\n")
        f.write(f"{'╚' + '═' * BOX_WIDTH + '╝'}\n")

        # Print active thresholds for reference
        f.write("\n" + f"{'┌' + '─' * BOX_WIDTH + '┐'}\n")
        f.write(f"│{'  AUTOMATION RULES':<{BOX_WIDTH}}│\n")
        f.write(f"│{'  ' + '─' * (BOX_WIDTH-2):<{BOX_WIDTH}}│\n")
        f.write(box_line("Temp > (AC ON)",      f"{THRESHOLDS['temperature_high']} °C"))
        f.write(box_line("Temp < (Heater ON)",  f"{THRESHOLDS['temperature_low']} °C"))
        f.write(box_line("Humidity > (Dehum.)", f"{THRESHOLDS['humidity_high']} %"))
        f.write(box_line("Humidity < (Hum.)",   f"{THRESHOLDS['humidity_low']} %"))
        f.write(box_line("Light < (Lights ON)", f"{THRESHOLDS['light_low']} lux"))
        f.write(box_line("Light > (Blinds)",    f"{THRESHOLDS['light_high']} lux"))
        f.write(box_line("Motion (Security)",   "DETECTED"))
        f.write(f"{'└' + '─' * BOX_WIDTH + '┘'}\n")

def log_text(reading, number, alerts):
    with open(TEXT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'┌' + '─' * BOX_WIDTH + '┐'}\n")
        f.write(f"│{'  Reading # ' + str(number):<{BOX_WIDTH}}│\n")
        f.write(f"│{'  ' + '─' * (BOX_WIDTH-2):<{BOX_WIDTH}}│\n")
        f.write(box_line("Timestamp",   reading["timestamp"]))
        f.write(box_line("Temperature", reading["temperature"], "°C"))
        f.write(box_line("Humidity",    reading["humidity"], "%"))
        f.write(box_line("Motion",
                         "DETECTED" if reading["motion"] == 1 else "NO MOTION"))
        f.write(box_line("Light",       reading["light"], "lux"))
        f.write(f"│{'  ' + '─' * (BOX_WIDTH-2):<{BOX_WIDTH}}│\n")

        if alerts:
            f.write(f"│{'  AUTOMATION ACTIONS TRIGGERED':^{BOX_WIDTH}}│\n")
            for a in alerts:
                line = f"  [{a['severity']}] {a['sensor']}: {a['action']}"
                f.write(f"│{line:<{BOX_WIDTH}}│\n")
        else:
            f.write(f"│{'  STATUS: ALL NORMAL — No actions triggered':<{BOX_WIDTH}}│\n")

        f.write(f"{'└' + '─' * BOX_WIDTH + '┘'}\n")

def write_summary(readings, all_alerts_list):
    temperatures   = [r["temperature"] for r in readings]
    humidities     = [r["humidity"]    for r in readings]
    lights         = [r["light"]       for r in readings]
    motion_events  = sum(r["motion"]   for r in readings)
    total_alerts   = sum(len(a)        for a in all_alerts_list)
    critical_count = sum(
        1 for batch in all_alerts_list
          for a in batch
          if a["severity"] == "CRITICAL"
    )

    action_counts = {}
    for batch in all_alerts_list:
        for a in batch:
            action_counts[a["action"]] = action_counts.get(a["action"], 0) + 1

    with open(TEXT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'╔' + '═' * BOX_WIDTH + '╗'}\n")
        f.write(f"║{'AUTOMATION SUMMARY':^{BOX_WIDTH}}║\n")
        f.write(f"{'╠' + '═' * BOX_WIDTH + '╣'}\n")
        f.write(box_line("Total Readings",    len(readings)))
        f.write(box_line("Total Alerts",      total_alerts))
        f.write(box_line("Critical Alerts",   critical_count))
        f.write(box_line("Motion Events",     motion_events))
        f.write(box_line("Avg Temperature",
                         f"{sum(temperatures)/len(temperatures):.2f}", "°C"))
        f.write(box_line("Avg Humidity",
                         f"{sum(humidities)/len(humidities):.2f}", "%"))
        f.write(box_line("Avg Light",
                         f"{sum(lights)/len(lights):.2f}", "lux"))
        f.write(f"{'╠' + '═' * BOX_WIDTH + '╣'}\n")
        f.write(f"║{'  ACTION FREQUENCY':^{BOX_WIDTH}}║\n")
        f.write(f"{'╠' + '═' * BOX_WIDTH + '╣'}\n")
        for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
            f.write(box_line(action[:22], count, "times"))
        f.write(f"{'╚' + '═' * BOX_WIDTH + '╝'}\n")

def init_alert_file():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ALERT_FILE, "w", encoding="utf-8") as f:
        f.write(f"IoT AUTOMATION ALERTS LOG — {now}\n")
        f.write("=" * 62 + "\n\n")

def log_alerts_file(reading, number, alerts):
    if not alerts:
        return
    with open(ALERT_FILE, "a", encoding="utf-8") as f:
        f.write(f"[Reading #{number}] @ {reading['timestamp']}\n")
        for a in alerts:
            f.write(
                f"  {a['icon']}  [{a['severity']:8}] "
                f"{a['sensor']:<12} "
                f"Value={a['value']:<12} "
                f"→ ACTION: {a['action']}\n"
            )
        f.write("\n")

# =========================================================
# TERMINAL DISPLAY
# =========================================================

SEVERITY_COLORS = {
    "CRITICAL" : "\033[91m",   # Red
    "WARNING"  : "\033[93m",   # Yellow
    "INFO"     : "\033[96m",   # Cyan
    "RESET"    : "\033[0m",
    "GREEN"    : "\033[92m",
    "BOLD"     : "\033[1m",
}

def color(text, key):
    return f"{SEVERITY_COLORS[key]}{text}{SEVERITY_COLORS['RESET']}"

def print_banner():
    print("\n" + "═" * 62)
    print(color(f"{'IoT AUTOMATION LOGIC — Decodelabs Task 4':^62}", "BOLD"))
    print("═" * 62)
    print(f"  Sensors    : Temperature | Humidity | Motion | Light")
    print(f"  Readings   : {TOTAL_READINGS} | Interval : {INTERVAL_SECONDS}s")
    print(f"  Thresholds : Temp {THRESHOLDS['temperature_low']}–{THRESHOLDS['temperature_high']}°C | "
          f"Hum {THRESHOLDS['humidity_low']}–{THRESHOLDS['humidity_high']}% | "
          f"Light {THRESHOLDS['light_low']}–{THRESHOLDS['light_high']} lux")
    print("═" * 62 + "\n")

def print_reading(reading, number, alerts):
    motion_str = "DETECTED" if reading["motion"] == 1 else "NO MOTION"

    print(f"  ┌─ Reading {number:02d} ── {reading['timestamp']} ─────────────────┐")
    print(f"  │  Temperature : {reading['temperature']:>6} °C                        │")
    print(f"  │  Humidity    : {reading['humidity']:>6} %                         │")
    print(f"  │  Motion      : {motion_str:<22}            │")
    print(f"  │  Light       : {reading['light']:>6} lux                       │")
    print(f"  ├─ AUTOMATION RESULT {'─'*39}┤")

    if alerts:
        for a in alerts:
            sev_colored = color(f"[{a['severity']:8}]", a["severity"])
            print(f"  │  {a['icon']}  {sev_colored}  {a['sensor']:<12} → {a['action']:<20}│")
    else:
        print(f"  │  {color('✔  [NORMAL  ]  All sensors within safe range', 'GREEN'):<58}│")

    print(f"  └{'─'*58}┘\n")

# =========================================================
# DASHBOARD
# =========================================================

def plot_dashboard(readings, all_alerts_list):

    numbers      = [r["n"]           for r in readings]
    temperatures = [r["temperature"] for r in readings]
    humidities   = [r["humidity"]    for r in readings]
    lights       = [r["light"]       for r in readings]
    motions      = [r["motion"]      for r in readings]
    alert_counts = [len(a)           for a in all_alerts_list]

    fig = plt.figure(figsize=(16, 10), facecolor="#f8fafc")

    fig.suptitle(
        "IoT Automation Logic Dashboard — Task 4",
        fontsize=18, fontweight="bold", color="#0f172a", y=0.98,
    )

    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.55, wspace=0.35)

    def style_ax(ax, title, ylabel, bg):
        ax.set_facecolor(bg)
        ax.set_title(title, fontsize=11, fontweight="bold",
                     color="#0f172a", pad=8)
        ax.set_xlabel("Reading No.", fontsize=9, color="#475569")
        ax.set_ylabel(ylabel,        fontsize=9, color="#475569")
        ax.set_xticks(numbers)
        ax.tick_params(labelsize=8, colors="#475569")
        ax.grid(True, linestyle="--", alpha=0.4, color="#cbd5e1")
        for sp in ax.spines.values():
            sp.set_edgecolor("#e2e8f0")

    def add_threshold_line(ax, value, label, color, linestyle="--"):
        ax.axhline(value, color=color, linewidth=1.4,
                   linestyle=linestyle, alpha=0.8, label=label)

    def annotate_points(ax, nums, vals, color):
        for x, y in zip(nums, vals):
            ax.annotate(f"{y}", (x, y), textcoords="offset points",
                        xytext=(0, 7), fontsize=7, ha="center", color=color)

    # ─── 1. Temperature ───────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(numbers, temperatures, color="#e63946", linewidth=2.2,
             marker="o", markersize=6, markerfacecolor="white",
             markeredgewidth=2, zorder=3)
    ax1.fill_between(numbers, temperatures, min(temperatures)-2,
                     alpha=0.12, color="#e63946")
    add_threshold_line(ax1, THRESHOLDS["temperature_high"],
                       f"HIGH ({THRESHOLDS['temperature_high']}°C)", "#e63946")
    add_threshold_line(ax1, THRESHOLDS["temperature_low"],
                       f"LOW  ({THRESHOLDS['temperature_low']}°C)", "#1d4ed8")
    annotate_points(ax1, numbers, temperatures, "#be123c")
    style_ax(ax1, "Temperature + Thresholds", "°C", "#fff5f5")
    ax1.set_ylim(min(temperatures)-5, max(temperatures)+10)
    ax1.legend(fontsize=7, loc="upper right")

    # ─── 2. Humidity ──────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(numbers, humidities, color="#1d4ed8", linewidth=2.2,
             marker="s", markersize=6, markerfacecolor="white",
             markeredgewidth=2, zorder=3)
    ax2.fill_between(numbers, humidities, min(humidities)-2,
                     alpha=0.12, color="#1d4ed8")
    add_threshold_line(ax2, THRESHOLDS["humidity_high"],
                       f"HIGH ({THRESHOLDS['humidity_high']}%)", "#7c3aed")
    add_threshold_line(ax2, THRESHOLDS["humidity_low"],
                       f"LOW  ({THRESHOLDS['humidity_low']}%)",  "#059669")
    annotate_points(ax2, numbers, humidities, "#1e40af")
    style_ax(ax2, "Humidity + Thresholds", "%", "#eff6ff")
    ax2.set_ylim(max(0, min(humidities)-5), min(100, max(humidities)+10))
    ax2.legend(fontsize=7, loc="upper right")

    # ─── 3. Light ─────────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(numbers, lights, color="#f59e0b", linewidth=2.2,
             marker="^", markersize=6, markerfacecolor="white",
             markeredgewidth=2, zorder=3)
    ax3.fill_between(numbers, lights, max(0, min(lights)-20),
                     alpha=0.12, color="#f59e0b")
    add_threshold_line(ax3, THRESHOLDS["light_high"],
                       f"BRIGHT ({THRESHOLDS['light_high']} lux)", "#dc2626")
    add_threshold_line(ax3, THRESHOLDS["light_low"],
                       f"DIM    ({THRESHOLDS['light_low']} lux)",  "#6366f1")
    annotate_points(ax3, numbers, lights, "#b45309")
    style_ax(ax3, "Light Intensity + Thresholds", "lux", "#fffbeb")
    ax3.set_ylim(max(0, min(lights)-50), min(1100, max(lights)+100))
    ax3.legend(fontsize=7, loc="upper right")

    # ─── 4. Motion Detection ──────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    bar_colors = ["#dc2626" if m == 1 else "#bbf7d0" for m in motions]
    ax4.bar(numbers, motions, color=bar_colors, width=0.6,
            edgecolor="white", linewidth=1.2)
    for i, (n, m) in enumerate(zip(numbers, motions)):
        if m == 1:
            ax4.text(n, 1.08, "ALERT", ha="center", fontsize=7,
                     fontweight="bold", color="#dc2626")
    style_ax(ax4, "Motion Detection", "Status", "#f0fdf4")
    ax4.set_ylim(0, 1.7)
    ax4.set_yticks([0, 1])
    ax4.set_yticklabels(["No Motion", "Detected"])

    # ─── 5. Alert Count per Reading ───────────────────
    ax5 = fig.add_subplot(gs[2, 0])
    alert_bar_colors = [
        "#dc2626" if c >= 3 else
        "#f59e0b" if c >= 1 else
        "#16a34a"
        for c in alert_counts
    ]
    bars = ax5.bar(numbers, alert_counts, color=alert_bar_colors,
                   width=0.6, edgecolor="white", linewidth=1.2)
    for bar, count in zip(bars, alert_counts):
        ax5.text(bar.get_x() + bar.get_width()/2,
                 count + 0.05, str(count),
                 ha="center", fontsize=9, fontweight="bold",
                 color="#0f172a")
    style_ax(ax5, "Alerts Triggered per Reading", "Alert Count", "#fef2f2")
    ax5.set_ylim(0, max(alert_counts) + 1.5 if max(alert_counts) > 0 else 3)
    legend_patches = [
        mpatches.Patch(color="#dc2626", label="≥ 3 alerts (Critical)"),
        mpatches.Patch(color="#f59e0b", label="1–2 alerts (Warning)"),
        mpatches.Patch(color="#16a34a", label="0 alerts (Normal)"),
    ]
    ax5.legend(handles=legend_patches, fontsize=7, loc="upper right")

    # ─── 6. Action Frequency Bar Chart ────────────────────
    ax6 = fig.add_subplot(gs[2, 1])
    action_counts = {}
    for batch in all_alerts_list:
        for a in batch:
            short = a["action"].replace("Turn ON ", "").replace("Turn ", "")
            action_counts[short] = action_counts.get(short, 0) + 1

    if action_counts:
        labels = list(action_counts.keys())
        values = list(action_counts.values())
        palette = ["#e63946","#1d4ed8","#f59e0b",
                   "#16a34a","#7c3aed","#0891b2","#dc2626"]
        colors  = [palette[i % len(palette)] for i in range(len(labels))]
        ax6.barh(labels, values, color=colors, edgecolor="white",
                 linewidth=1.2, height=0.5)
        for i, v in enumerate(values):
            ax6.text(v + 0.05, i, str(v), va="center",
                     fontsize=9, fontweight="bold", color="#0f172a")
        ax6.set_facecolor("#f8fafc")
        ax6.set_title("Automation Action Frequency", fontsize=11,
                      fontweight="bold", color="#0f172a", pad=8)
        ax6.set_xlabel("Times Triggered", fontsize=9, color="#475569")
        ax6.tick_params(labelsize=8, colors="#475569")
        ax6.set_xlim(0, max(values) + 1.5)
        ax6.grid(True, axis="x", linestyle="--", alpha=0.4, color="#cbd5e1")
        for sp in ax6.spines.values():
            sp.set_edgecolor("#e2e8f0")
    else:
        ax6.text(0.5, 0.5, "No Alerts Triggered",
                 ha="center", va="center", fontsize=12,
                 color="#16a34a", transform=ax6.transAxes)
        style_ax(ax6, "Automation Action Frequency", "", "#f0fdf4")

    total_alerts   = sum(alert_counts)
    critical_count = sum(
        1 for batch in all_alerts_list
          for a in batch if a["severity"] == "CRITICAL"
    )
    summary = (
        f"Total Alerts: {total_alerts}   |   "
        f"Critical: {critical_count}   |   "
        f"Readings: {TOTAL_READINGS}   |   "
        f"Rules Active: 7"
    )
    fig.text(0.5, 0.005, summary, ha="center", fontsize=9.5,
             color="#334155",
             bbox=dict(facecolor="white", edgecolor="#cbd5e1",
                       boxstyle="round,pad=0.5", alpha=0.9))

    plt.savefig(GRAPH_FILE, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print(f"\n  Dashboard saved → {GRAPH_FILE}")
    plt.show()

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print_banner()
    init_csv()
    init_text()
    init_alert_file()

    all_readings    = []
    all_alerts_list = []

    for number in range(1, TOTAL_READINGS + 1):

        reading = read_sensors()
        reading["n"] = number

        # ── Task 4: evaluate automation rules ──
        alerts = evaluate_rules(reading)

        # ── Display ─────────────────────────────────
        print_reading(reading, number, alerts)

        # ── Logging ─────────────────────────────────
        log_csv(reading, number, alerts)
        log_text(reading, number, alerts)
        log_alerts_file(reading, number, alerts)

        all_readings.append(reading)
        all_alerts_list.append(alerts)

        time.sleep(INTERVAL_SECONDS)

    write_summary(all_readings, all_alerts_list)

    total = sum(len(a) for a in all_alerts_list)
    normals = sum(1 for a in all_alerts_list if len(a) == 0)

    print("═" * 62)
    print(color(f"{'AUTOMATION COMPLETE':^62}", "BOLD"))
    print("═" * 62)
    print(f"  Total Readings   : {TOTAL_READINGS}")
    print(f"  Total Alerts     : {total}")
    print(f"  Normal Readings  : {normals}")
    print(f"  CSV Saved        : {CSV_FILE}")
    print(f"  Report Saved     : {TEXT_FILE}")
    print(f"  Alert Log Saved  : {ALERT_FILE}")
    print(f"  Dashboard Saved  : {GRAPH_FILE}")
    print("═" * 62 + "\n")

    plot_dashboard(all_readings, all_alerts_list)