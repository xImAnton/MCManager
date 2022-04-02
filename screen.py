import pathlib
import os
import re

SCREEN_NAME = re.compile(r"[0-9]+\.(mc-.+)")


def get_running_servers() -> list[str]:
    screen_dir = pathlib.Path(f"/run/screen/S-{os.getlogin()}")

    if not screen_dir.is_dir():
        return []

    return [s.name for s in screen_dir.glob("*.mc-*")]
