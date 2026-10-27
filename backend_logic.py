"""
Backend logic for the Security Command Builder application.
"""

import json
import os

DEFAULT_TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools_data")

MANDATORY_FLAG_MAP = {
    "ffuf": {
        "Target URL": "-u",
        "Wordlist": "-w",
    },
}

POSITIONAL_BEFORE_FLAGS = set()

# Flags that must be concatenated directly with their value (e.g., -T4 instead of -T 4)
NO_SPACE_FLAGS = {
    ("Nmap", "-T"),
}


def load_tools_data(tools_dir=DEFAULT_TOOLS_DIR):
    """Read every *.json file inside `tools_dir` and merge them into a single dict."""
    combined_data = {}

    if os.path.exists(tools_dir):
        for file_name in sorted(os.listdir(tools_dir)):
            if file_name.endswith(".json"):
                file_path = os.path.join(tools_dir, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tool_json = json.load(f)
                        combined_data.update(tool_json)
                except Exception as e:
                    print(f"Error loading {file_name}: {e}")

    return combined_data


def persist_tool_data(tool_name, tools_data, tools_dir=DEFAULT_TOOLS_DIR, error_context="update"):
    """Write the current in-memory definition of `tool_name` back to its JSON file."""
    file_path = os.path.join(tools_dir, f"{tool_name.lower()}.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        file_data[tool_name] = tools_data[tool_name]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(file_data, f, indent=4, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"Error {error_context}: Could not update JSON file. Details: {e}")
        return False


def get_selected_flag_values(flag_widgets):
    """Return a dict of {flag: value} for every checked and visible flag."""
    selected = {}
    for fw in flag_widgets:
        if fw["var"].get() and fw.get("is_visible", True):
            if fw["entry"]:
                if fw["is_dropdown"]:
                    val = fw["opt_var"].get()
                else:
                    val = fw["entry"].get().strip()
                selected[fw["flag"]] = val
            else:
                selected[fw["flag"]] = ""
    return selected


def get_mandatory_values(mandatory_widgets):
    """Return a dict of {label: value} for the current tool's mandatory field widgets."""
    return {mw["label"]: mw["entry"].get().strip() for mw in mandatory_widgets}


def build_command_string(tool_name, tool_info, flag_widgets, mandatory_widgets):
    """Build the full command-line string for `tool_name`."""
    base = tool_info.get("base_command", "tool")
    flag_map = MANDATORY_FLAG_MAP.get(tool_name, {})

    selected_flags = []
    for fw in flag_widgets:
        if fw["var"].get() and fw.get("is_visible", True):
            flag_str = fw["flag"]
            if fw["entry"]:
                if fw["is_dropdown"]:
                    val = fw["opt_var"].get()
                else:
                    val = fw["entry"].get().strip()

                if val:
                    if (tool_name, flag_str) in NO_SPACE_FLAGS:
                        selected_flags.append(f"{flag_str}{val}")
                    else:
                        selected_flags.append(f"{flag_str} {val}")
                else:
                    selected_flags.append(flag_str)
            else:
                selected_flags.append(flag_str)

    flag_bound_parts = []
    positional_parts = []
    for mw in mandatory_widgets:
        label = mw["label"]
        value = mw["entry"].get().strip()
        display_value = value if value else f"[{label}]"

        if label in flag_map:
            flag_bound_parts.append(f"{flag_map[label]} {display_value}")
        else:
            positional_parts.append(display_value)

    all_flags = flag_bound_parts + selected_flags

    if tool_name in POSITIONAL_BEFORE_FLAGS:
        command_parts = [base] + positional_parts + all_flags
    else:
        command_parts = [base] + all_flags + positional_parts

    return " ".join(command_parts)