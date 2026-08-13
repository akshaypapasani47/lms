import re


def get_safe_username(username):
    return re.sub(
        r"[^a-zA-Z0-9_.-]",
        "_",
        username
    )