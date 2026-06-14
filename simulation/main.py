import os
import sys
import time
import json
import random
import csv
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from rich.console import Console
    from rich.table import Table as RichTable
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.text import Text
except ImportError:
    print("[ERROR] Missing modules. Run: pip install paho-mqtt reportlab rich")
    sys.exit(1)

console = Console()

# Resolve structural paths dynamically
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))
data_dir = os.path.join(root_dir, "data")
reports_dir = os.path.join(root_dir, "reports")

os.makedirs(data_dir, exist_ok=True)
os.makedirs(reports_dir, exist_ok=True)

MQTT_HOST_BROKER = "broker.hivemq.com"
MQTT_HOST_PORT = 1883
TELEMETRY_TOPIC = "home/energy/simulated_node1"
DATA_LOG_CSV = os.path.join(data_dir, "historical_energy_log.csv")
PDF_REPORT_PATH = os.path.join(reports_dir, "energy_consumption_report.pdf")
LOCAL_ENERGY_UNIT_TARIFF = 7.50

class ApplianceModel:
    def __init__(self, name, watts, variance=0.05):
        self.name = name; self.watts = watts; self.variance = variance; self.active = False
    def get_reading(self):
        return self.watts * (1.0 + random.uniform(-self.variance, self.variance)) if self.active else 0.0

appliances = [
    ApplianceModel("HVAC System", 2200.0, 0.10),
    ApplianceModel("Refrigerator", 280.0, 0.04),
    ApplianceModel("Water Boiler", 3000.0, 0.02),
    ApplianceModel("IT Infrastructure", 150.0, 0.01)
]

def generate_pdf_report(kwh, cost, records):
    doc = SimpleDocTemplate(PDF_REPORT_PATH, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=22, textColor=colors.HexColor("#1A365D"), spaceAfter=12)
    story.append(Paragraph("Smart Home Energy Analytics Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    data = [
        [Paragraph("<b>Metric Dimension</b>", styles["Normal"]), Paragraph("<b>Aggregated Value</b>", styles["Normal"])],
        ["Samples Data Points", str(records)],
        ["Net Energy Consumed", f"{kwh:.4f} kWh"],
        ["Financial Impact Cost", f"Rs. {cost:.2f}"]
    ]
    t = Table(data, colWidths=[240, 240])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (1,0), colors.HexColor("#2B6CB0")),
        ("TEXTCOLOR", (0,0), (1,0), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0"))
    ]))
    story.append(t)
    doc.build(story)

def run_simulation():
    console.print(Panel.fit("⚡ INITIALIZING SCADA TELEMETRY MONITOR SYSTEM\n[Mode: Rolling Production Matrix Output Stream]", style="bold cyan", border_style="blue"))
    
    # 1. System Boot Progress
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), transient=True) as progress:
        task1 = progress.add_task("[cyan]Connecting cloud broker node...", total=100)
        while not progress.finished:
            time.sleep(0.01)
            progress.update(task1, advance=3)

    mqtt_client = mqtt.Client()
    try:
        mqtt_client.connect(MQTT_HOST_BROKER, MQTT_HOST_PORT, 60)
        mqtt_client.loop_start()
    except:
        pass
        
    with open(DATA_LOG_CSV, mode="w", newline="") as f:
        csv.writer(f).writerow(["timestamp","Voltage","Current","Power","Cumulative_kWh","Cost_INR","Status"])
        
    # Master Table Header Configuration
    table = RichTable(header_style="bold white on blue", box=None)
    table.add_column("Timestamp Log", justify="center", width=20)
    table.add_column("Voltage", justify="right", width=12)
    table.add_column("Current", justify="right", width=12)
    table.add_column("Active Power", justify="right", width=16)
    table.add_column("Energy Index", justify="right", width=18)
    table.add_column("Accrued Cost", justify="right", width=15)
    table.add_column("Status Alert", justify="center", width=18)
    
    # Header print kar rahe hain
    console.print(table)
    
    wh = 0.0
    ticks = 0
    appliances[1].active = True
    appliances[3].active = True
    
    try:
        while ticks < 30:
            ticks += 1
            if ticks == 5: appliances[0].active = True   # AC starts
            if ticks == 15: appliances[2].active = True  # Boiler starts (Spike trigger)
            if ticks == 24: appliances[2].active = False # Load shed
            
            w = sum(app.get_reading() for app in appliances)
            v = random.uniform(229.0, 231.8)
            i = w / v
            wh += (w * (1.0 / 3600.0))
            kwh = wh / 1000.0
            cost = kwh * LOCAL_ENERGY_UNIT_TARIFF
            status = "NORMAL" if i <= 22.0 else "OVERLOAD_TRIP"
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Dynamic Row Color Mapping based on electrical values
            v_str = f"[magenta]{v:.1f} V[/magenta]"
            i_str = f"[yellow]{i:.2f} A[/yellow]"
            w_str = f"[green]{w:.1f} W[/green]"
            kwh_str = f"[bold green]{kwh:.5f} kWh[/bold green]"
            cost_str = f"[bold white]₹ {cost:.2f}[/bold white]"
            
            if status == "NORMAL":
                status_str = "[bold green]● OPERATIONAL[/bold green]"
            else:
                status_str = "[bold blink red]⚠ RELAY TRIP[/bold blink red]"
                w_str = f"[bold red]{w:.1f} W[/bold red]"
                i_str = f"[bold red]{i:.2f} A[/bold red]"

            # Printing each entry sequentially line by line
            console.print(f"{ts}  │  {v_str}  │  {i_str}  │  {w_str}  │  {kwh_str}  │  {cost_str}  │  {status_str}")
            
            with open(DATA_LOG_CSV, mode="a", newline="") as f:
                csv.writer(f).writerow([ts, f"{v:.2f}", f"{i:.3f}", f"{w:.2f}", f"{kwh:.6f}", f"{cost:.4f}", status])
            
            if mqtt_client.is_connected():
                mqtt_client.publish(TELEMETRY_TOPIC, json.dumps({"v":v,"i":i,"w":w,"kwh":kwh,"status":status}))
            time.sleep(1)
    finally:
        mqtt_client.loop_stop()
        generate_pdf_report(kwh, cost, ticks)
        console.print(Panel("[SUCCESS] Telemetry session captured.\nLogs written cleanly to data/ and reports/.", title="System Base", border_style="green"))

if __name__ == "__main__":
    run_simulation()