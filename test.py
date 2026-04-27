import json

with open("_data/votes/2026-04.json", "r") as f:
    data = json.load(f)

for x in data:
    if x["name"] == "Ambulance":
        print(f"Ambulance source in json: {repr(x['source'])}")

import csv
with open("votes/votes_2026-04.csv", "r") as f:
    reader = csv.reader(f)
    for row in reader:
        for i in range(3):
            base = 3 + i * 3
            if base >= len(row): break
            if row[base].strip() == "Ambulance":
                print(f"Ambulance source in csv: {repr(row[base+1])}")
