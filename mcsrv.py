#!/usr/bin/python3
import os

import click
from click import echo

from server import ServerInformation, check_ram_argument


def get_server(ctx: click.Context) -> ServerInformation:
    return ServerInformation(ctx.obj["SERVER_PATH"])


@click.group(help="Control your Minecraft Servers with ease!")
@click.option("--dir", "-p", "server_path", help="set the directory of the current server", default=os.getcwd(),
              type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.pass_context
def main(ctx: click.Context, server_path: str):
    ctx.ensure_object(dict)
    ctx.obj["SERVER_PATH"] = server_path


@main.group(help="start the current server", invoke_without_command=True)
@click.option("--ram", "-r", "ram_",
              help="specifies how much ram this server is given (overrides default if specified)", default=None,
              type=click.STRING)
@click.option("--console", "-c", "open_console", help="attach to the servers console after it started", is_flag=True,
              default=False)
@click.pass_context
def start(ctx: click.Context, ram_: str, open_console: bool):
    if ctx.invoked_subcommand is not None:
        return

    server = get_server(ctx)

    if server.running:
        server.print("server is already running")
        return

    server.start(ram=ram_)

    if not server.running:
        server.print("error while starting")
        return

    server.print("successfully started")

    if open_console:
        server.print("attaching to console")
        server.open_console()


@start.command(name="auto", help="start all servers that should be autostarted")
def start_auto():
    for server in ServerInformation.get_registered_servers():
        server = ServerInformation(server)

        if server.autostarts and not server.running:
            server.start()


@main.command(help="stop the current server")
@click.pass_context
def stop(ctx):
    server = get_server(ctx)

    if not server.running:
        server.print("server is not running")
        return

    server.send_command("stop")
    server.print("stopping")


@main.command(help="show the console of the current server")
@click.pass_context
def console(ctx: click.Context):
    server = get_server(ctx)

    if not server.running:
        server.print("server needs to be started first")
        return

    server.open_console()


@main.command(help="show information about the current server")
@click.pass_context
def info(ctx: click.Context):
    server = get_server(ctx)
    cpu, ram_ = server.get_stats()

    server.print(f"""Information:
  ID:            {server.id}
  Path:          {server.path}
  Jar-File:      {server.jar}
  Running:       {server.running}
  Screen-Handle: {server.screen_handle}
  Max-RAM:       {server.ram}
  CPU-Usage:     {cpu}%
  RAM-Usage:     {ram_}GB
  Autostart:     {server.autostarts}""")


@main.group(help="get/set whether this server is started with the system", invoke_without_command=True)
@click.pass_context
def autostart(ctx: click.Context):
    if ctx.invoked_subcommand is not None:
        return

    server = get_server(ctx)
    server.print(
        f"autostart is currently {'enabled' if server.data.get('autostart', 'false').lower() == 'true' else 'disabled'}")


@autostart.command(name="on", help="enable autostart for the current server")
@click.pass_context
def autostart_on(ctx: click.Context):
    server = get_server(ctx)
    server.data["autostart"] = "true"
    server.save_data()
    server.print("autostart has been enabled")


@autostart.command(name="off", help="enable autostart for the current server")
@click.pass_context
def autostart_off(ctx: click.Context):
    server = get_server(ctx)
    server.data["autostart"] = "false"
    server.save_data()
    server.print("autostart has been disabled")


@main.command(help="get/set how much ram this server is allocated")
@click.argument("ram_value", type=click.STRING, required=False, nargs=1)
@click.pass_context
def ram(ctx: click.Context, ram_value: str):
    server = get_server(ctx)

    if ram_value is None:
        server.print(f"currently allocated ram: {server.ram}")
        return

    server.data["ram"] = check_ram_argument(ram_value)
    server.save_data()
    server.print(f"set ram to {server.data['ram']}")


@main.command(name="list", help="list all registered servers")
def list_():
    echo("mcsrv: all servers:")
    for server in ServerInformation.get_registered_servers():
        server = ServerInformation(server)
        echo(f"  {server.id} -> {server.path}")


@main.command(help="list all running servers")
def ps():
    echo("mcsrv: running servers:")
    for server in ServerInformation.get_registered_servers():
        server = ServerInformation(server)

        if not server.running:
            continue

        echo(f"  {server.id}")


if __name__ == '__main__':
    main(obj={})
