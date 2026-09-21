# filter_flows.py
input_file = "recvd-flows.txt"
output_file = "flows_under_100.txt"

with open(input_file, "r") as f_in, open(output_file, "w") as f_out:
    for line in f_in:
        line = line.strip()
        if not line:
            continue

        try:
            # Extract fields by splitting on commas
            fields = [x.strip() for x in line.split(",")]

            # Parse values into a dictionary
            data = {}
            for field in fields:
                if ":" in field:
                    key, val = field.split(":", 1)
                    data[key.strip()] = val.strip()

            flowsize = int(data["flowsize"])
            if flowsize < 100:
                src = data["src"]
                dst = data["dst"]
                starttime = data["starttime"]
                finishtime = data["finishtime"]
                fct = data["fct"]

                # Write in requested format
                f_out.write(f"({src},{dst},{flowsize},{starttime},{finishtime},{fct})\n")

        except Exception:
            continue
