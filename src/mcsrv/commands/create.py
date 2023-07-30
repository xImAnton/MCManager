import os

import dispenser
from dispenser.impl import VERSION_PROVIDERS

from ..server import Server
from ..util import is_valid_ram_argument
from ..prompt import prompt_user, yesno, valid_yesno


# TODO: prompt for autostart

def setup_server_interactively(s: Server):
    settings = prompt_user({
        "port": {
            "prompt": "Port",
            "default": "25565",
            "validate": str.isnumeric,
            "clean": str.strip
        },
        "motd": {
            "prompt": "MOTD",
            "default": "A Minecraft Server",
            "clean": str.strip
        },
        "cmd": {
            "prompt": "Enable command blocks [y/n]",
            "validate": valid_yesno,
            "clean": [yesno, str, str.lower],
            "default": "y"
        },
        "whitelist": {
            "prompt": "Enable whitelist [y/n]",
            "validate": valid_yesno,
            "clean": [yesno, str, str.lower],
            "default": "n"
        },
        "ram": {
            "prompt": "Allocated RAM",
            "default": "4G",
            "validate": is_valid_ram_argument,
        },
        "ops": {
            "prompt": "OP Players (comma separated) [NOT IMPLEMENTED]",
            "default": ""
        },  # TODO
        "pvp": {
            "prompt": "Enable pvp [y/n]",
            "validate": valid_yesno,
            "clean": [yesno, str, str.lower],
            "default": "y"
        },
        "maxplayer": {
            "prompt": "Max player count",
            "default": "20",
            "validate": str.isnumeric,
            "clean": str.strip
        },
        "flight": {
            "prompt": "Allow flight [y/n]",
            "validate": valid_yesno,
            "clean": [yesno, str, str.lower],
            "default": "y"
        }
    })

    s.properties.set_value("server-port", settings["port"])
    s.properties.set_value("motd", settings["motd"])
    s.properties.set_value("enable-command-block", settings["cmd"])
    s.properties.set_value("white-list", settings["whitelist"])
    s.properties.set_value("pvp", settings["pvp"])
    s.properties.set_value("max-players", settings["maxplayer"])
    s.properties.set_value("allow-flight", settings["flight"])

    s.properties.save()

    s.ram = settings["ram"]


def create(name: str, version: tuple[str], interactive: bool, newest: bool):
    dispenser.init()

    if os.path.exists(name) and not (os.path.isdir(name) and not os.listdir(name)):
        print("mcsrv: directory/file already exists")
        return

    if not os.path.isdir(name):
        os.mkdir(name)

    avail = None

    if len(version) == 0:
        avail = VERSION_PROVIDERS.keys()
    elif len(version) == 1 and newest:
        prov = VERSION_PROVIDERS[version[0]]
        version = prov.NAME, prov.get_newest_major(), prov.get_newest_minor(prov.get_newest_major())
    elif len(version) == 1:
        avail = VERSION_PROVIDERS[version[0]].get_major_versions()
    elif len(version) == 2 and newest:
        prov = VERSION_PROVIDERS[version[0]]
        version = prov.NAME, version[1], prov.get_newest_minor(version[1])
    elif len(version) == 2:
        avail = VERSION_PROVIDERS[version[0]].get_minor_versions(version[1])

    if avail is not None:
        print(f"mcsrv: available versions: {' '.join(avail)}")
        return

    print(f"mcsrv: creating {' '.join(version)} server")
    dispenser.dispense(version[0], version[1], version[2], name)
    s = Server(name).register()

    s.version = version

    if interactive:
        setup_server_interactively(s)

    s.print("server created")
