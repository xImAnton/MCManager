package util

import (
	"os/exec"
	"strings"
)

func GetRunningScreens() []string {
	cmd := exec.Command("screen", "-list")
	stdout, err := cmd.Output()

	if err != nil {
		return make([]string, 0)
	}

	lines := strings.Split(string(stdout), "\n")
	var screens []string

	for _, line := range lines[1 : len(lines)-2] {
		words := strings.Fields(strings.TrimSpace(line))
		screens = append(screens, words[0])
	}

	return screens
}

func ExecCommandInScreen(id string, cmd string) error {
	command := exec.Command("screen", "-S", id, "-p", "0", "-X", "stuff", cmd+"^M")
	err := command.Run()
	return err
}
