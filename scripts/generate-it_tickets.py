import json
import random
from datetime import datetime, timedelta

# Semiconductor-specific ticket templates
tickets = []

categories = {
    "equipment_maintenance": [
        "KLA {tool} calibration failed with error {code}",
        "Wafer alignment issue on {tool} at fab {location}",
        "Recipe load failure for {process} on tool {tool}"
    ],
    "it_security": [
        "VPN access request for {role} at {location}",
        "Suspicious login attempt from IP {ip}",
        "Certificate renewal for {service} expired"
    ],
    "data_analytics": [
        "Query timeout on {dataset} returning {rows} rows",
        "Pipeline failed at step {step} for {process}",
        "Dashboard {name} not refreshing data"
    ]
}

tools = ["2950", "2960", "SpectraShape", "Archer", "eDR-7000"]
locations = ["Austin", "Milpitas", "Singapore", "Taipei", "Regensburg"]
processes = ["etch", "deposition", "lithography", "metrology", "inspection"]

for i in range(50):
    category = random.choice(list(categories.keys()))
    template = random.choice(categories[category])
    
    ticket = {
        "ticket_id": f"INC{datetime.now().strftime('%Y%m')}{str(i).zfill(4)}",
        "title": template.format(
            tool=random.choice(tools),
            code=random.randint(1000, 9999),
            location=random.choice(locations),
            process=random.choice(processes),
            role=random.choice(["engineer", "manager", "technician"]),
            ip=f"10.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            service=random.choice(["API Gateway", "Auth Service", "Data Lake"]),
            dataset=random.choice(["wafer_measurements", "tool_logs", "defect_images"]),
            rows=random.randint(10000, 1000000),
            step=random.randint(1, 10),
            name=random.choice(["Fab Ops", "Quality Metrics", "Yield Analysis"])
        ),
        "description": f"Detailed description of the issue...",
        "priority": random.choice(["P1", "P2", "P3", "P4"]),
        "status": random.choice(["Open", "In Progress", "Resolved"]),
        "created_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
        "assigned_to": f"team_{random.choice(['ops', 'security', 'data', 'hardware'])}"
    }
    tickets.append(ticket)

with open("data/raw/json/it_tickets.json", "w") as f:
    json.dump(tickets, f, indent=2)

print(f" Generated {len(tickets)} mock IT tickets")