package subcommands

import (
	"MCManager/util"
	"errors"
	"fmt"
	"github.com/urfave/cli/v2"
)

var (
	ErrServerNotRunning = errors.New("the current server is not running")
)

func StopServer(c *cli.Context) error {
	info, err := GetCurrentServerInfo()
	if err != nil {
		return cli.Exit(err, 1)
	}

	if !info.Running() {
		return cli.Exit(ErrServerNotRunning, 1)
	}

	err = util.ExecCommandInScreen(info.ScreenName(), "stop")
	if err != nil {
		return cli.Exit(err, 1)
	}

	fmt.Println("server stopped")
	return nil
}
