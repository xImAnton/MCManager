#!/usr/bin/python3
import os

import click
from click import echo
from colorama import Fore, Style, Back

from .javaexecutable import JavaExecutable, prompt_java_version
from .server import Server


def get_server(ctx: click.Context) -> Server:
    return Server(ctx.obj["SERVER_PATH"]).register()


@click.group(help="Control your Minecraft Servers with ease!")
@click.option("--dir", "-p", "server_path", help="Set the directory in which to search for the server", default=os.getcwd(),
              type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.pass_context
def main(ctx: click.Context, server_path: str):
    ctx.ensure_object(dict)
    ctx.obj["SERVER_PATH"] = server_path


@main.group(help="Start the Server", invoke_without_command=True)
@click.option("--ram", "-r", "ram_",
              help="Specifies how much RAM this server is allocated on start (overrides default if specified)", default=None,
              type=click.STRING)
@click.option("--console", "-c", "open_console", help="Attach to the servers console after start", is_flag=True,
              default=False)
@click.pass_context
def start(ctx: click.Context, ram_: str, open_console: bool):
    if ctx.invoked_subcommand is not None:
        return

    server = get_server(ctx)

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


@start.command(name="auto", help="Start all Servers that should be autostarted")
def start_auto():
    for server in Server.get_registered_servers():
        if server.autostarts and not server.running:
            server.start()


@main.command(help="Stop the Server")
@click.pass_context
def stop(ctx):
    server = get_server(ctx)

    if not server.running:
        server.print(f"{Fore.YELLOW}Server is not running")
        return

    server.send_command("stop")
    server.print("Stopping...")


@main.command(help="Open the Server console")
@click.pass_context
def console(ctx: click.Context):
    server = get_server(ctx)

    if not server.running:
        server.print(f"{Fore.YELLOW}Server needs to be started first")
        return

    server.open_console()


@main.command(help="Show information about the Server")
@click.pass_context
def info(ctx: click.Context):
    server = get_server(ctx)

    server.print("Measuring performance...")
    cpu, ram_ = server.get_stats()

    server.print(f"""Information:
  {Style.BRIGHT}ID:{Style.RESET_ALL}            {server.id}
  {Style.BRIGHT}Path:{Style.RESET_ALL}          {server.path}
  {Style.BRIGHT}Jar-File:{Style.RESET_ALL}      {server.jar}
  {Style.BRIGHT}Running:{Style.RESET_ALL}       {server.running}
  {Style.BRIGHT}Screen-Handle:{Style.RESET_ALL} {server.screen_handle}
  {Style.BRIGHT}Max-RAM:{Style.RESET_ALL}       {server.ram}
  {Style.BRIGHT}CPU-Usage:{Style.RESET_ALL}     {cpu}%
  {Style.BRIGHT}RAM-Usage:{Style.RESET_ALL}     {ram_}GB
  {Style.BRIGHT}Autostart:{Style.RESET_ALL}     {server.autostarts}
  {Style.BRIGHT}Java-Version:{Style.RESET_ALL}  {server.java_executable}""")


@main.group(help="Get/Set whether the Server is started with the system", invoke_without_command=True)
@click.pass_context
def autostart(ctx: click.Context):
    if ctx.invoked_subcommand is not None:
        return

    server = get_server(ctx)
    server.print(
        f"Autostart is currently {Style.BRIGHT}{'enabled' if server.data.get('autostart', 'false').lower() == 'true' else 'disabled'}")


@autostart.command(name="on", help="Enable autostart for the Server")
@click.pass_context
def autostart_on(ctx: click.Context):
    server = get_server(ctx)
    server.autostarts = True
    server.print(f"Autostart has been {Style.BRIGHT}enabled")


@autostart.command(name="off", help="Disable autostart for the Server")
@click.pass_context
def autostart_off(ctx: click.Context):
    server = get_server(ctx)
    server.autostarts = False
    server.print(f"Autostart has been {Style.BRIGHT}disabled")


@main.command(help="Get/Set how much RAM this Server is allocated")
@click.argument("ram_value", type=click.STRING, required=False, nargs=1)
@click.pass_context
def ram(ctx: click.Context, ram_value: str):
    server = get_server(ctx)

    if ram_value is None:
        server.print(f"Currently allocated RAM: {Style.BRIGHT}{server.ram}")
        return

    server.ram = ram_value
    server.print(f"Set RAM to {Style.BRIGHT}{server.data['ram']}")


@main.command(name="list", help="Get a list of running Servers")
@click.option("--all", "-a", "list_all", help="List all Servers (including offline Servers)", is_flag=True,
              default=False)
def list_(list_all: bool):
    # TODO: print as table with offline/online indicator

    for server in Server.get_registered_servers():
        if list_all or server.running:
            echo(f"  {server.id} -> {server.path}")


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
@click.pass_context
def set_java_version(ctx: click.Context, java_version_path: str):
    server = get_server(ctx)

    if java_version_path is None:
        java_version_path = prompt_java_version()

    try:
        new_java = JavaExecutable(java_version_path).register()
    except ValueError:
        raise click.exceptions.Exit(code=1)

    server.java_executable = new_java
    server.print(f"Java version set to {Style.BRIGHT}{new_java.version!r}")

    if server.running:
        server.print("Note that you have to restart the Server for changes to apply")


if __name__ == '__main__':
    main(obj={})
