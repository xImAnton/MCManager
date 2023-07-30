#!/usr/bin/python3
import functools
import os
from typing import Optional

import click
import dispenser
import tabulate
from click import echo
from colorama import Fore, Style

from .commands import create, start, start_auto
from .javaexecutable import JavaExecutable, prompt_java_version
from .server import Server, ALL_LIST_PROPERTIES
from .util import format_server_info, format_enabled


def get_server(ctx: click.Context) -> Server:
    return Server(ctx.obj["SERVER_PATH"]).register()


def pass_server(f):
    @functools.wraps(f)
    @click.pass_context
    def wrapped(ctx: click.Context, *args, **kwargs):
        return f(get_server(ctx), *args, **kwargs)

    return wrapped


@click.group(help="Control your Minecraft Servers with ease!")
@click.option("--dir", "-p", "server_path", help="Set the directory in which to search for the server",
              default=os.getcwd(),
              type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.pass_context
def main(ctx: click.Context, server_path: str):
    ctx.ensure_object(dict)
    ctx.obj["SERVER_PATH"] = server_path


@main.command(name="create", help="Create a new server")
@click.argument("name", type=click.STRING, required=True, nargs=1)
@click.argument("version", type=click.STRING, required=False, nargs=-1)
@click.option("--interactive", "-i", "interactive", is_flag=True, default=True)
@click.option("--newest", "-n", "newest", is_flag=True, default=False)
def create_cmd(name: str, version: tuple[str], interactive: bool, newest: bool):
    create(name, version, interactive, newest)


@main.group(name="update", help="Update the server")
@pass_server
def update(server: Server):
    if server.version is None:
        server.print("updating is only supported on servers created using mcsrv")
        raise click.exceptions.Exit(code=-1)

    if server.running:
        server.print("server must be stopped before updating")
        raise click.exceptions.Exit(code=-1)

    dispenser.init()


@update.command(name="major", help="Update major version")
@click.argument("new_major", type=click.STRING, required=False, nargs=1)
@pass_server
def update_major(server: Server, new_major: Optional[str]):
    server.version = dispenser.update_major(server.data["software"], server.path, new_major)


@update.command(name="minor", help="Update minor version")
@click.argument("new_minor", type=click.STRING, required=False, nargs=1)
@pass_server
def update_minor(server: Server, new_minor: Optional[str]):
    server.version = dispenser.update_minor(server.data["software"], server.path, server.data["major"], new_minor)


@main.group(name="start", help="Start the Server", invoke_without_command=True)
@click.option("--ram", "-r", "ram_",
              help="Specifies how much RAM this server is allocated on start (overrides default if specified)",
              default=None,
              type=click.STRING)
@click.option("--console", "-c", "open_console", help="Attach to the servers console after start", is_flag=True,
              default=False)
@pass_server
@click.pass_context
def start_cmd(ctx, server: Server, ram_: str, open_console: bool):
    if ctx.invoked_subcommand is not None:
        return

    start(server, ram_, open_console)


@start_cmd.command(name="auto", help="Start all Servers that should be autostarted")
def start_auto_cmd():
    start_auto()


@main.command(name="stop", help="Stop the Server")
@pass_server
def stop(server: Server):
    if not server.running:
        server.print(f"{Fore.YELLOW}Server is not running")
        return

    server.stop()
    server.print("Stopping...")


@main.command(name="console", help="Open the Server console")
@pass_server
def console(server: Server):
    if not server.running:
        server.print(f"{Fore.YELLOW}Server needs to be started first")
        return

    server.open_console()


@main.command(help="Show information about the Server")
@pass_server
def info(server: Server):
    server.print("Measuring performance...")
    cpu, ram_ = server.get_stats()

    server.print(format_server_info({
        "ID": server.id,
        "Path": server.path,
        "Launch-Method": server.launch_method[0],
        "Launch-Arguments": server.launch_method[1],
        "Running": server.running,
        "Screen-Handle": server.screen_handle,
        "Allocated RAM": f"{server.ram}B",
        "CPU-Usage": f"{cpu}%",
        "RAM-Usage": f"{ram_}GB",
        "Autostart": server.autostarts,
        "Java-Version": server.java_executable,
        "Player Count": server.player_count
    }))


@main.group(help="Get/Set whether the Server is started with the system", invoke_without_command=True)
@click.argument("enable", type=click.BOOL, required=False, nargs=1)
@pass_server
def autostart(server: Server, enable: Optional[bool]):
    if enable is None:
        server.print(
            f"Autostart is currently {format_enabled(server.data.get('autostart', 'false').lower() == 'true')}")
        return

    server.autostarts = enable
    server.print(f"Autostart has been {format_enabled(enable)}")


@main.command(help="Get/Set how much RAM this Server is allocated")
@click.argument("ram_value", type=click.STRING, required=False, nargs=1)
@pass_server
def ram(server: Server, ram_value: str):
    if ram_value is None:
        server.print(f"Currently allocated RAM: {Style.BRIGHT}{server.ram}")
        return

    server.ram = ram_value
    server.print(f"Set RAM to {Style.BRIGHT}{server.data['ram']}")
    server.print_restart_note()


@main.command(name="list", help="Get a list of running Servers")
@click.option("--running", "-r", "only_running", help="List only running Servers", is_flag=True,
              default=False)
@click.option("--plain", "-f", "plain", help="Plain output", is_flag=True,
              default=False)
@click.option("--props", "-p", "props", help=f"Specify the props to print ({ALL_LIST_PROPERTIES})", type=click.STRING, default="iproax")
@click.option("--all-props", "-a", "all_props", help="Show all props", is_flag=True, default=False)
def list_(only_running: bool, plain: bool, props: str, all_props: bool):
    data = []

    if all_props:
        props = ALL_LIST_PROPERTIES

    for server in Server.get_registered_servers():
        if not only_running or server.running:
            data.append(server.get_list_data(props, plain))

    fmt = "plain" if plain else "rounded_outline"

    header_names = {
        "i": "ID",
        "p": "Path",
        "r": "",
        "a": "Autostart",
        "t": "Type",
        "x": "CPU, RAM",
        "o": "Port",
        "j": "Java Version",
        "m": "Allocated RAM",
    }

    headers = [] if plain else [header_names[i] for i in ALL_LIST_PROPERTIES if i in props]

    echo(tabulate.tabulate(data, headers, tablefmt=fmt, numalign="left"))


@main.group(help="Manage Java Versions", invoke_without_command=True)
@click.pass_context
def java(ctx: click.Context):
    if ctx.invoked_subcommand is not None:
        return

    echo("Registered Java installations:")
    for j in JavaExecutable.get_known_java_installations():
        echo(f"  {j.version} ({j.path})")


@java.command(name="add", help="Register a Java Version")
@click.argument("path", type=click.STRING, required=True, nargs=1)
def add_java_version(path: str):
    try:
        new_java = JavaExecutable(path).register()
    except ValueError:
        raise click.exceptions.Exit(code=1)

    echo(f"{new_java} has been registered")


@java.command(name="set", help="Set the Java Version of the Server")
@click.argument("java_version_path", type=click.STRING, required=False, nargs=1)
@pass_server
def set_java_version(server: Server, java_version_path: str):
    if java_version_path is None:
        java_version_path = prompt_java_version()

    try:
        new_java = JavaExecutable(java_version_path).register()
    except ValueError:
        raise click.exceptions.Exit(code=1)

    server.java_executable = new_java
    server.print(f"Java version set to {Style.BRIGHT}{new_java.version!r}")
    server.print_restart_note()


@main.command(name="properties", help="Read and change server properties")
@click.argument("key", type=click.STRING, required=True, nargs=1)
@click.argument("value", type=click.STRING, required=False, nargs=1)
@click.option("--strip", "-f", "strip", help="Format output for easier interpreting by machines", is_flag=True,
              default=False)
@pass_server
def properties_cmd(server: Server, key: str, value: str, strip: bool):
    # TODO: implement `strip`

    if not value:  # print value
        if key not in server.properties:
            server.print(f"not defined: {key}")
            raise click.exceptions.Exit(1)

        server.print(f"{key} is {Style.BRIGHT}{server.properties.get_value(key)}{Style.RESET_ALL}")
        return

    # set key to value
    prev_val = server.properties.get_value(key)
    server.properties.set_value(key, value, save=True)
    server.print(
        f"changed {key} from {Style.BRIGHT}{prev_val}{Style.RESET_ALL} to {Style.BRIGHT}{value}{Style.RESET_ALL}")
    server.print_restart_note()


@main.command(name="port", help="Set/get the server port")
@click.argument("port", type=click.INT, required=False, nargs=1)
@pass_server
def port_(server: Server, port: Optional[int]):
    if not port:
        server.print(f"current port: {Style.BRIGHT}{server.properties.get_value('server-port')}{Style.RESET_ALL}")
        return

    server.properties.set_value("server-port", port, save=True)
    server.print(f"server port is now {Style.BRIGHT}{port}{Style.RESET_ALL}")
    server.print_restart_note()


@main.command(name="commandblocks", help="Enable/disable command blocks")
@click.argument("enable", type=click.BOOL, required=False, nargs=1)
@pass_server
def commandblocks_(server: Server, enable: Optional[bool]):
    if enable is None:
        server.print(
            f"command blocks are currently {format_enabled(server.properties.get_value('enable-command-block') == 'true')}")
        return

    server.properties.set_value("enable-command-block", "true" if enable else "false", save=True)
    server.print(f"command blocks are now {format_enabled(enable)}")
    server.print_restart_note()


@main.command(name="html", help="Start the Browser Version of mcsrv")
@click.option("--port", "-p", "port", type=click.INT, default=9117)
@click.option("--debug", "-d", "debug", type=click.BOOL, default=False, is_flag=True)
def start_html(port: int, debug: bool):
    from .api import app

    app.run("127.0.0.1", port, debug=debug, load_dotenv=False)


@main.command(name="dir", help="Print the directory of the server")
@click.argument("server_id", type=click.STRING, required=True, nargs=1)
def get_server_dir(server_id: str):
    server = Server.get_by_id(server_id)

    echo(server.path)


if __name__ == '__main__':
    main(obj={})
