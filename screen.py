import os
import pathlib
import re

SCREEN_NAME = re.compile(r"[0-9]+\.(mc-.+)")


class Screen:
    def __init__(self, sock: str):
        s = sock.split(".", 1)
        self.pid: int = int(s[0])
        self.name: str = s[1]

    def __repr__(self):
        return f"{self.pid}.{self.name}"

    def __str__(self):
        return self.__repr__()


def get_running_servers() -> list[Screen]:
    screen_dir = pathlib.Path(f"/run/screen/S-{os.getlogin()}")

    if not screen_dir.is_dir():
        return []

    return [Screen(s.name) for s in screen_dir.glob("*.mc-*")]
