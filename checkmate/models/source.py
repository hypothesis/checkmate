from enum import Enum


class Source(Enum):
    """An enum for the places a rule hit can come from."""

    URL_HAUS = "url_haus"
    BLOCK_LIST = "block_list"
    ALLOW_LIST = "allow_list"
