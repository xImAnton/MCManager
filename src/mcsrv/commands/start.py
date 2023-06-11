from colorama import Fore, Back

from ..server import Server


def start(server: Server, ram_: str, open_console: bool):
    if server.running:
        server.print(f"{Fore.YELLOW}Server is already running")
        return

    server.start(ram=ram_)

    if not server.running:
        server.print(f"{Fore.RED}An unknown error occurred while starting the Server")
        return

    server.print(f"Successfully started the Server")

    if not open_console:
        server.print(f"View the console with {Back.BLUE}{Fore.WHITE}mcsrv console")
        return

    server.print("Attaching to console")
    server.open_console()


def start_auto():
    for server in Server.get_registered_servers():
        if server.autostarts and not server.running:
            server.start()
