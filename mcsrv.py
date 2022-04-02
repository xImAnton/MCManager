#!/usr/bin/python3
import os

import click
from click import echo

from server import ServerInformation


@click.group(help="Control your Minecraft Servers with ease!")
@click.option("--dir", "-p", "server_path", help="the directory of the current server", default=os.getcwd(), type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.pass_context
def main(ctx: click.Context, server_path: str):
    ctx.ensure_object(dict)
    ctx.obj["SERVER"] = ServerInformation(server_path)


@main.command(help="start the current server")
@click.option("--ram", "-r", "ram_", help="specified how much ram this server is given (overrides default if specified)", default=None, type=click.STRING)
# TODO: @click.option("--console", "-c", help="attach to the servers console after it started", is_flag=True, default=False)
@click.pass_context
def start(ctx: click.Context, ram_: str):
    server: ServerInformation = ctx.obj["SERVER"]

    if server.running:
        echo("server is already running")
        return

    server.start(ram=ram_)

    if server.running:
        echo("server successfully started")
        return

    echo("error while starting server")


@main.command(help="stop the current server")
@click.pass_context
def stop(ctx):
    server: ServerInformation = ctx.obj["SERVER"]

    if not server.running:
        echo("server is not running")
        return

    server.send_command("stop")
    echo("stopping server")


@main.command(help="show the console of the current server")
def console():
    pass


@main.command(help="show information about the current server")
@click.pass_context
def info(ctx: click.Context):
    server: ServerInformation = ctx.obj["SERVER"]

    print(f"""Server Information:
      Jar-File:    {server.jar}
      ID:          {server.id}
      Running:     {server.running}
      Path:        {server.path}
      Screen-Name: {server.screen_name}
    """)


@main.command(help="get/set whether this server is started with the system")
def autostart():
    pass


@main.command(help="get/set how much ram this server is allocated")
def ram():
    pass


@main.command(name="list", help="list all registered servers")
def list_():
    pass


@main.command(help="list all running servers")
def ps():
    pass


if __name__ == '__main__':
    main(obj={})
