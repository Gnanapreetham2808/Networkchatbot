import json
from pathlib import Path

SOURCE_FILE = Path("cisco_nl2cli.json")
TARGET_FILE = Path("nl2cli_extended.json")
SWITCH_NAME = "INVIJB1SW1"
CITY = "Vijayawada"
BUILDING_ID = 1

# Phrases for building/city variants
BUILDING_TEMPLATES = [
    "for building {b} in {city}",
    "in {city} building {b}",
]

def load_source():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Source dataset {SOURCE_FILE} not found.")
    with SOURCE_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Source dataset must be a list of objects.")
    return data


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def ensure_target_suffix(cmd: str) -> str:
    suffix = f"--target {SWITCH_NAME}"
    if suffix in cmd:
        return cmd
    # If command already has arguments, just append a space then suffix
    return f"{cmd.strip()} {suffix}".strip()


def build_variants(entry):
    base_input = entry.get("input", "").strip()
    base_output = entry.get("output", "").strip()

    variants = []

    # 1. Original
    variants.append({"input": base_input, "output": base_output})

    # 2. Explicit switch name (append phrase to input, add --target to output)
    if f"on {SWITCH_NAME}" not in base_input:
        input_switch = normalize_space(f"{base_input} on {SWITCH_NAME}")
        output_switch = ensure_target_suffix(base_output)
        variants.append({"input": input_switch, "output": output_switch})

    # 3 & 4. Building / city variants (two templates at least)
    output_with_target = ensure_target_suffix(base_output)
    for tmpl in BUILDING_TEMPLATES:
        phrase = tmpl.format(city=CITY, b=BUILDING_ID)
        input_building = normalize_space(f"{base_input} {phrase}")
        variants.append({"input": input_building, "output": output_with_target})

    return variants


def extend_dataset(data):
    extended = []
    seen = set()  # to avoid duplicates
    for entry in data:
        for var in build_variants(entry):
            key = (var["input"].lower(), var["output"].lower())
            if key not in seen:
                seen.add(key)
                extended.append(var)
    return extended


def main():
    source = load_source()
    extended = extend_dataset(source)
    with TARGET_FILE.open("w", encoding="utf-8") as f:
        json.dump(extended, f, indent=2, ensure_ascii=False)
    print(f"Extended dataset written to {TARGET_FILE} with {len(extended)} pairs (from {len(source)} originals).")


if __name__ == "__main__":
    main()
