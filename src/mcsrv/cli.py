#!/usr/bin/python3
import os

import click
import inquirer
from click import echo

from .javaversion import JavaVersion
from .server import Server


def get_server(ctx: click.Context) -> Server:
    return Server(ctx.obj["SERVER_PATH"]).register()


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
    for server in Server.get_registered_servers():
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

    server.print("measuring performance")
    cpu, ram_ = server.get_stats()

    server.print(f"""information:
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
    server.autostarts = True
    server.print("autostart has been enabled")


@autostart.command(name="off", help="disable autostart for the current server")
@click.pass_context
def autostart_off(ctx: click.Context):
    server = get_server(ctx)
    server.autostarts = False
    server.print("autostart has been disabled")


@main.command(help="get/set how much ram this server is allocated")
@click.argument("ram_value", type=click.STRING, required=False, nargs=1)
@click.pass_context
def ram(ctx: click.Context, ram_value: str):
    server = get_server(ctx)

    if ram_value is None:
        server.print(f"currently allocated ram: {server.ram}")
        return

    server.ram = ram_value
    server.print(f"set ram to {server.data['ram']}")


@main.command(name="list", help="list all registered servers")
def list_():
    echo("mcsrv: all servers:")
    for server in Server.get_registered_servers():
        echo(f"  {server.id} -> {server.path}")


@main.command(help="list all running servers")
def ps():
    echo("mcsrv: running servers:")
    for server in Server.get_registered_servers():

        if not server.running:
            continue

        echo(f"  {server.id}")


@main.group(help="manage java versions", invoke_without_command=True)
@click.pass_context
def java(ctx: click.Context):
    if ctx.invoked_subcommand is not None:
        return

    versions = JavaVersion.get_known_java_installations()

    echo("registered java installations:")
    for j in versions:
        echo(f"  {j.version} ({j.path})")


@java.command(name="add")
@click.argument("path", type=click.STRING, required=True, nargs=1)
@click.pass_context
def add_java_version(ctx: click.Context, path: str):
    try:
        new_java = JavaVersion(path).register()
    except ValueError:
        raise click.exceptions.Exit(code=1)

    echo(f"java at {new_java.path!r} (version: {new_java.version!r}) has been registered")


@java.command(name="set")
@click.argument("java_version_path", type=click.STRING, required=False, nargs=1)
@click.pass_context
def set_java_version(ctx: click.Context, java_version_path: str):
    server = get_server(ctx)

    if java_version_path is None:
        installations = JavaVersion.get_known_java_installations()

        if len(installations) == 0:
            echo("no registered java installations. please register one or pass the path as an argument")
            raise click.exceptions.Exit(code=1)

        if len(installations) == 1:
            echo("nothing changed, there is only one registered java version. if you want to run this server on another, register it or pass the path as an argument")
            return

        options = [(f"{j.version} ({j.path})", j.path) for j in installations]

        answer = inquirer.prompt([inquirer.List("java_ver", message="Which java version should be used?", choices=options)])

        if not answer:
            raise click.exceptions.Exit(code=1)

        java_version_path = answer["java_ver"]

    try:
        new_java = JavaVersion(java_version_path).register()
    except ValueError:
        raise click.exceptions.Exit(code=1)

    server.java_bin = new_java.path

    if server.running:
        server.print("note that you have to restart the server for changes to apply")


if __name__ == '__main__':
    main(obj={})
