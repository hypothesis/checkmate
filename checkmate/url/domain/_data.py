from pkg_resources import resource_stream


def load_data(filename):
    with resource_stream("checkmate", filename) as handle:
        return [line.strip().decode("utf-8") for line in handle]
