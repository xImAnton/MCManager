package subcommands

import (
	"errors"
	"github.com/urfave/cli/v2"
	"os"
)

var (
	ErrStartingConsole = errors.New("there was an error while starting the console")
)

func ShowServerConsole(c *cli.Context) error {
	info, err := GetCurrentServerInfo()
	if err != nil {
		return cli.Exit(err, 1)
	}

	proc, err := os.StartProcess("screen", []string{"-x", info.ScreenName()}, &os.ProcAttr{
		Dir: info.Path,
	})

	if err != nil {
		return cli.Exit(ErrStartingConsole, 1)
	}

	_, err = proc.Wait()

	return err
}
