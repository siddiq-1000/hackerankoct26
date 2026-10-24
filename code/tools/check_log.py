import re
from pathlib import Path

def parse_log():
    log_path = Path("log.txt")
    if not log_path.exists():
        print("log.txt not found!")
        return

    text = log_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    entries = []
    current_entry = None

    for line in lines:
        if line.startswith("## [") and "]" in line:
            if current_entry:
                entries.append(current_entry)
            current_entry = {"header": line, "body": []}
        elif current_entry is not None:
            current_entry["body"].append(line)

    if current_entry:
        entries.append(current_entry)

    print(f"Total structured log entries found: {len(entries)}")
    print("=" * 80)
    for idx, e in enumerate(entries, 1):
        hdr = e["header"]
        body_text = "\n".join(e["body"])
        tool_m = list(re.finditer(r"\ntool=([^\r\n]+)", body_text))
        model_m = list(re.finditer(r"\nmodel=([^\r\n]+)", body_text))
        tool_val = tool_m[-1].group(1).strip() if tool_m else "MISSING"
        model_val = model_m[-1].group(1).strip() if model_m else "MISSING"
        print(f"{idx:2d}. {hdr[:70]}")
        print(f"    tool={tool_val} | model={model_val}")
    print("=" * 80)

if __name__ == "__main__":
    parse_log()
