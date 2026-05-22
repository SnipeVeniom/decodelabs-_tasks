import random
import csv
import time
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

TOTAL_READINGS   = 10
INTERVAL_SECONDS = 1

CSV_FILE   = "sensor_log.csv"
TEXT_FILE  = "sensor_report.txt"
GRAPH_FILE = "iot_dashboard.png"

_state = {
    "temperature" : 28.0,   # comfortable room start °C
    "humidity"    : 55.0,   # normal indoor start %
    "light"       : 400.0,  # moderate indoor start lux
    "motion_cool" : 0,      # cooldown counter (readings)
}

def simulate_temperature():
    if random.random() < 0.03:               
        _state["temperature"] += random.choice([-2.0, 2.0])
    else:
        _state["temperature"] += random.uniform(-0.8, 0.8)
    _state["temperature"] = max(20.0, min(40.0, _state["temperature"]))
    return round(_state["temperature"], 2)

def simulate_humidity():
    if random.random() < 0.03:
        _state["humidity"] += random.choice([-8.0, 8.0])
    else:
        _state["humidity"] += random.uniform(-1.2, 1.2)
    _state["humidity"] = max(30.0, min(90.0, _state["humidity"]))
    return round(_state["humidity"], 2)

def simulate_light():
    if random.random() < 0.03:
        _state["light"] += random.choice([-200.0, 200.0])
    else:
        _state["light"] += random.uniform(-40.0, 40.0)
    _state["light"] = max(0.0, min(1000.0, _state["light"]))
    return round(_state["light"], 2)

def simulate_motion():
    if _state["motion_cool"] > 0:
        _state["motion_cool"] -= 1
        return 0
    detected = random.choices([0, 1], weights=[80, 20])[0]
    if detected:
        _state["motion_cool"] = 2
    return detected

def read_sensors():
    return {
        "timestamp"   : datetime.now().strftime("%H:%M:%S"),
        "temperature" : simulate_temperature(),
        "humidity"    : simulate_humidity(),
        "motion"      : simulate_motion(),
        "light"       : simulate_light(),
    }


def init_csv():
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "No.",
            "Timestamp",
            "Temperature (°C)",
            "Humidity (%)",
            "Motion",
            "Light (lux)"
        ])

def log_csv(reading, number):
    motion_status = (
        "DETECTED"
        if reading["motion"] == 1
        else "NO MOTION"
    )
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            number,
            reading["timestamp"],
            reading["temperature"],
            reading["humidity"],
            motion_status,
            reading["light"]
        ])

# =========================================================
# TEXT REPORT
# =========================================================

BOX_WIDTH = 54

def txt_line(label, value, unit=""):
    value_string = f"{value} {unit}".strip()
    content      = f"  {label:<18}: {value_string}"
    return f"│{content:<{BOX_WIDTH}}│\n"

def init_text():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(TEXT_FILE, "w", encoding="utf-8") as file:
        file.write("\n")
        file.write(f"{'╔' + '═' * BOX_WIDTH + '╗'}\n")
        file.write(f"║{'IoT SENSOR DATA MONITORING REPORT':^{BOX_WIDTH}}║\n")
        file.write(f"║{'Decodelabs IoT Internship - Task 2':^{BOX_WIDTH}}║\n")
        file.write(f"║{('Generated: ' + now):^{BOX_WIDTH}}║\n")
        file.write(f"{'╚' + '═' * BOX_WIDTH + '╝'}\n")

def log_text(reading, number):
    motion_status = (
        "DETECTED"
        if reading["motion"] == 1
        else "NO MOTION"
    )
    with open(TEXT_FILE, "a", encoding="utf-8") as file:
        file.write(f"\n{'┌' + '─' * BOX_WIDTH + '┐'}\n")
        file.write(f"│{'  Reading # ' + str(number):<{BOX_WIDTH}}│\n")
        file.write(f"│{'  ' + '─' * (BOX_WIDTH - 2):<{BOX_WIDTH}}│\n")
        file.write(txt_line("Timestamp",   reading["timestamp"]))
        file.write(txt_line("Temperature", reading["temperature"], "°C"))
        file.write(txt_line("Humidity",    reading["humidity"],    "%"))
        file.write(txt_line("Motion",      motion_status))
        file.write(txt_line("Light",       reading["light"],       "lux"))
        file.write(f"{'└' + '─' * BOX_WIDTH + '┘'}\n")

def write_summary(readings):
    temperatures = [r["temperature"] for r in readings]
    humidities   = [r["humidity"]    for r in readings]
    lights       = [r["light"]       for r in readings]
    motions      = [r["motion"]      for r in readings]

    with open(TEXT_FILE, "a", encoding="utf-8") as file:
        file.write(f"\n{'╔' + '═' * BOX_WIDTH + '╗'}\n")
        file.write(f"║{'SUMMARY':^{BOX_WIDTH}}║\n")
        file.write(f"{'╠' + '═' * BOX_WIDTH + '╣'}\n")
        file.write(txt_line("Total Readings",  len(readings)))
        file.write(txt_line("Avg Temperature",
                             f"{sum(temperatures)/len(temperatures):.2f}", "°C"))
        file.write(txt_line("Max Temperature",
                             f"{max(temperatures):.2f}", "°C"))
        file.write(txt_line("Min Temperature",
                             f"{min(temperatures):.2f}", "°C"))
        file.write(txt_line("Avg Humidity",
                             f"{sum(humidities)/len(humidities):.2f}", "%"))
        file.write(txt_line("Avg Light",
                             f"{sum(lights)/len(lights):.2f}", "lux"))
        file.write(txt_line("Motion Events",   sum(motions)))
        file.write(f"{'╚' + '═' * BOX_WIDTH + '╝'}\n")

# =========================================================
# TERMINAL DISPLAY
# =========================================================

def print_banner():
    print("\n" + "═" * 58)
    print(f"{'IoT SENSOR SIMULATION - Decodelabs Task 2':^58}")
    print("═" * 58)
    print("  Sensors  : Temperature | Humidity | Motion | Light")
    print(f"  Readings : {TOTAL_READINGS} | Interval : {INTERVAL_SECONDS}s")
    print(f"  CSV      : {CSV_FILE}")
    print(f"  Report   : {TEXT_FILE}")
    print("═" * 58 + "\n")

def print_reading(reading, number):
    motion_status = (
        "DETECTED"
        if reading["motion"] == 1
        else "NO MOTION"
    )
    print(
        f"  ┌─ Reading {number:02d} ─── "
        f"{reading['timestamp']} ───────────────┐"
    )
    print(f"  │  Temperature : {reading['temperature']:>6} °C              │")
    print(f"  │  Humidity    : {reading['humidity']:>6} %               │")
    print(f"  │  Motion      : {motion_status:<20}│")
    print(f"  │  Light       : {reading['light']:>6} lux             │")
    print(f"  └{'─' * 50}┘")

# =========================================================
# GRAPH  (Task 3 — Dashboard)
# =========================================================

def plot_dashboard(readings):
    numbers      = [r["n"]           for r in readings]
    temperatures = [r["temperature"] for r in readings]
    humidities   = [r["humidity"]    for r in readings]
    lights       = [r["light"]       for r in readings]
    motions      = [r["motion"]      for r in readings]

    fig = plt.figure(figsize=(14, 8), facecolor="#f8fafc")
    fig.suptitle(
        "IoT Sensor Monitoring Dashboard",
        fontsize=18, fontweight="bold", color="#0f172a", y=0.98,
    )

    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    # ── shared axis styler ────────────────────────────────
    def style_ax(ax, title, ylabel, background):
        ax.set_facecolor(background)
        ax.set_title(title, fontsize=12, fontweight="bold",
                     color="#0f172a", pad=8)
        ax.set_xlabel("Reading No.", fontsize=9, color="#475569")
        ax.set_ylabel(ylabel,        fontsize=9, color="#475569")
        ax.set_xticks(numbers)
        ax.tick_params(labelsize=8, colors="#475569")
        ax.grid(True, linestyle="--", alpha=0.4, color="#cbd5e1")
        for spine in ax.spines.values():
            spine.set_edgecolor("#e2e8f0")

    # ── Temperature ───────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(numbers, temperatures, color="#e63946", linewidth=2.2,
             marker="o", markersize=6, markerfacecolor="white",
             markeredgewidth=2)
    ax1.fill_between(numbers, temperatures, min(temperatures)-2,
                     alpha=0.12, color="#e63946")
    for x, y in zip(numbers, temperatures):
        ax1.annotate(f"{y}", (x, y), textcoords="offset points",
                     xytext=(0, 7), fontsize=7, ha="center", color="#be123c")
    style_ax(ax1, "Temperature", "°C", "#fff5f5")
    ax1.set_ylim(min(temperatures)-5, max(temperatures)+8)

    # ── Humidity ──────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(numbers, humidities, color="#1d4ed8", linewidth=2.2,
             marker="s", markersize=6, markerfacecolor="white",
             markeredgewidth=2)
    ax2.fill_between(numbers, humidities, min(humidities)-2,
                     alpha=0.12, color="#1d4ed8")
    for x, y in zip(numbers, humidities):
        ax2.annotate(f"{y}", (x, y), textcoords="offset points",
                     xytext=(0, 7), fontsize=7, ha="center", color="#1e40af")
    style_ax(ax2, "Humidity", "%", "#eff6ff")
    ax2.set_ylim(max(0, min(humidities)-5), min(100, max(humidities)+8))

    # ── Light ─────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(numbers, lights, color="#f59e0b", linewidth=2.2,
             marker="^", markersize=6, markerfacecolor="white",
             markeredgewidth=2)
    ax3.fill_between(numbers, lights, min(lights)-10,
                     alpha=0.12, color="#f59e0b")
    for x, y in zip(numbers, lights):
        ax3.annotate(f"{y}", (x, y), textcoords="offset points",
                     xytext=(0, 7), fontsize=7, ha="center", color="#b45309")
    style_ax(ax3, "Light Intensity", "lux", "#fffbeb")
    ax3.set_ylim(max(0, min(lights)-50), min(1100, max(lights)+80))

    # ── Motion Detection ──────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    bar_colors = ["#16a34a" if m == 1 else "#bbf7d0" for m in motions]
    bars = ax4.bar(numbers, motions, color=bar_colors, width=0.6,
                   edgecolor="white", linewidth=1.2)
    for bar, motion in zip(bars, motions):
        if motion == 1:
            ax4.text(
                bar.get_x() + bar.get_width() / 2,
                1.05, "YES", ha="center", fontsize=8, color="#15803d"
            )
    style_ax(ax4, "Motion Detection", "Status", "#f0fdf4")
    ax4.set_ylim(0, 1.6)
    ax4.set_yticks([0, 1])
    ax4.set_yticklabels(["No Motion", "Detected"])

    avg_temp     = sum(temperatures) / len(temperatures)
    avg_humidity = sum(humidities)   / len(humidities)
    avg_light    = sum(lights)       / len(lights)
    motion_count = sum(motions)

    summary = (
        f"Avg Temp: {avg_temp:.1f}°C   |   "
        f"Avg Humidity: {avg_humidity:.1f}%   |   "
        f"Avg Light: {avg_light:.0f} lux   |   "
        f"Motion Events: {motion_count}"
    )
    fig.text(
        0.5, 0.01, summary, ha="center", fontsize=9.5, color="#334155",
        bbox=dict(facecolor="white", edgecolor="#cbd5e1",
                  boxstyle="round,pad=0.5", alpha=0.9)
    )

    plt.savefig(GRAPH_FILE, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print(f"\n  Graph saved -> {GRAPH_FILE}")
    plt.show()


if __name__ == "__main__":

    print_banner()
    init_csv()
    init_text()

    all_readings = []

    for number in range(1, TOTAL_READINGS + 1):

        reading = read_sensors()
        reading["n"] = number

        print_reading(reading, number)
        log_csv(reading, number)
        log_text(reading, number)

        all_readings.append(reading)

        time.sleep(INTERVAL_SECONDS)

    write_summary(all_readings)

    print("\n" + "═" * 58)
    print(f"{'SIMULATION COMPLETE':^58}")
    print("═" * 58)
    print(f"  Total Readings : {TOTAL_READINGS}")
    print(f"  CSV Saved      : {CSV_FILE}")
    print(f"  Report Saved   : {TEXT_FILE}")
    print(f"  Graph Saved    : {GRAPH_FILE}")
    print("═" * 58 + "\n")

    plot_dashboard(all_readings)