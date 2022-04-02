package main

import (
	"MCManager/subcommands"
	"github.com/urfave/cli/v2"
	"log"
	"os"
)

// detect mc server in current directory, save ram in dotfile
// generate `screen` command. manage autostarts

func main() {
	app := &cli.App{
		Name:  "MCManager",
		Usage: "Manage Minecraft Servers",
		Commands: []*cli.Command{
			{
				Name:   "start",
				Action: subcommands.StartServer,
				Usage:  "Start the current Server",
			},
			{
				Name:   "console",
				Action: subcommands.ShowServerConsole,
				Usage:  "Show the console of the current server if it's running",
			},
			{
				Name:   "stop",
				Action: subcommands.StopServer,
				Usage:  "Stop the current Server",
			},
			{
				Name:   "info",
				Action: subcommands.ShowServerInfo,
				Usage:  "Show information about the current server",
			},
		},
	}

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
