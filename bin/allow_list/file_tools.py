import json


def load_json(filename):
    with open(filename) as handle:
        return json.load(handle)


def load_text(filename):
    with open(filename) as lines:
        for line in lines:
            line = line.strip()
            if line:
                yield line


def save_text(filename, lines):
    with open(filename, "w") as handle:
        for lines in sorted(lines):
            handle.write(f"{lines}\n")


def save_json(filename, data):
    with open(filename, "w") as handle:
        json.dump(data, handle, sort_keys=True, indent=4)
