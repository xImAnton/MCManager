package subcommands

import (
	"errors"
	"fmt"
	"github.com/urfave/cli/v2"
	"os/exec"
)

var (
	ErrServerAlreadyRunning = errors.New("server is already running")
	ErrErrorWhileStarting   = errors.New("couldn't start server")
)

func StartServer(c *cli.Context) error {
	info, err := GetCurrentServerInfo()
	if err != nil {
		return err
	}

	if info.Running() {
		return ErrServerAlreadyRunning
	}

	cmd := exec.Command("screen", "-d", "-S", info.ScreenName(), "-m", "java", "-Xmx4G", "-jar", info.JarFile)
	err = cmd.Run()
	if err != nil {
		return cli.Exit(err, 1)
	}

	if info.Running() {
		fmt.Println("server started")
		return nil
	}

	// error
	return cli.Exit(ErrErrorWhileStarting, 1)
}
