import os

import dispenser
from dispenser.impl import VERSION_PROVIDERS

from ..server import Server


def create(name: str, version: tuple[str]):
    dispenser.init()

    if os.path.exists(name) and not (os.path.isdir(name) and not os.listdir(name)):
        print("directory/file already exists")
        return

    if not os.path.isdir(name):
        os.mkdir(name)

    avail = None

    if len(version) == 0:
        avail = VERSION_PROVIDERS.keys()
    elif len(version) == 1:
        avail = VERSION_PROVIDERS[version[0]].get_major_versions()
    elif len(version) == 2:
        avail = VERSION_PROVIDERS[version[0]].get_minor_versions(version[1])

    if avail is not None:
        print(f"available versions: {' '.join(avail)}")
        return

    dispenser.dispense(version[0], version[1], version[2], name)

    s = Server(name).register()

    s.print("server created")
