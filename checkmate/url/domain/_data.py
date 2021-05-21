import importlib_resources


def load_data(filename):
    file_ref = importlib_resources.files("checkmate") / filename

    with importlib_resources.as_file(file_ref):
        with open(file_ref) as handle:
            return [line.strip() for line in handle]
