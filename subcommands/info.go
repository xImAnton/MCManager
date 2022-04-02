package subcommands

import (
	"MCManager/util"
	"errors"
	"fmt"
	"github.com/manifoldco/promptui"
	"github.com/urfave/cli/v2"
	"io/ioutil"
	"os"
	"path"
	"strings"
)

var (
	ErrNotAServerDir = errors.New("no server found in the current directory")
	ErrNoJarFound    = errors.New("no server jar found in the current directory")
)

type ServerInfo struct {
	JarFile string
	ID      string
	Path    string
}

type StoredData map[string]string

func (info *ServerInfo) Running() bool {
	screens := util.GetRunningScreens()

	for _, screen := range screens {
		name := strings.SplitN(screen, ".", 2)[1]
		if name == info.ScreenName() {
			return true
		}
	}

	return false
}

const DataFile = ".mcsrvmeta"

func (info *ServerInfo) DataFile() string {
	return path.Join(info.Path, DataFile)
}

func (info *ServerInfo) GetStoredData() (StoredData, error) {
	dat, err := os.ReadFile(info.DataFile())
	if err != nil {
		return nil, err
	}

	lines := string(dat)
	out := make(StoredData)

	for _, line := range strings.Split(lines, "\n") {
		line = strings.TrimSpace(line)

		if strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}

		out[parts[0]] = parts[1]
	}

	return out, nil
}

func (info *ServerInfo) SaveData(data StoredData) error {
	file, err := os.Create(info.DataFile())
	if err != nil {
		return err
	}

	defer func(file *os.File) {
		err := file.Close()
		if err != nil {
			panic(err)
		}
	}(file)

	for key, value := range data {
		_, err := file.WriteString(key + "=" + value + "\n")
		if err != nil {
			continue
		}
	}

	return file.Sync()
}

func (info *ServerInfo) ScreenName() string {
	return "mc-" + info.ID
}

func locateServerJarFile(info *ServerInfo) (string, error) {
	if storedData, err := info.GetStoredData(); err == nil {
		if val, ok := storedData["jar"]; ok {
			if util.IsFile(path.Join(info.Path, val)) {
				return val, nil
			}
			fmt.Printf("Cached file %q does not exist", val)
		}
	}

	var jarFiles []string
	files, err := ioutil.ReadDir(info.Path)

	for _, file := range files {
		if strings.HasSuffix(file.Name(), ".jar") {
			jarFiles = append(jarFiles, file.Name())
		}
	}

	if len(jarFiles) == 0 {
		return "", ErrNoJarFound
	}

	if len(jarFiles) == 1 {
		return jarFiles[0], nil
	}

	prompt := promptui.Select{
		Label: "Select Jar-File that runs the Server",
		Items: jarFiles,
	}

	_, selectedJar, err := prompt.Run()

	if err != nil {
		return "", err
	}

	data := make(StoredData)
	data["jar"] = selectedJar

	err = info.SaveData(data)
	if err != nil {
		return "", err
	}
	return selectedJar, err
}

func GetCurrentServerInfo() (*ServerInfo, error) {
	cwd, err := os.Getwd()
	if err != nil {
		return &ServerInfo{}, err
	}

	_, id := path.Split(cwd)
	if err != nil {
		return &ServerInfo{}, err
	}

	out := &ServerInfo{
		Path: cwd,
		ID:   id,
	}

	jarFile, err := locateServerJarFile(out)
	if err != nil {
		return out, err
	}

	out.JarFile = jarFile

	// save server dir to ~/.mcsrvrc
	_ = util.SaveServerPath(out.Path)

	return out, nil
}

func ShowServerInfo(c *cli.Context) error {
	info, err := GetCurrentServerInfo()

	if err != nil {
		if errors.Is(err, ErrNotAServerDir) {
			err.Error()
		}

		return cli.Exit(err, 1)
	}

	fmt.Printf("Current Server Information:\n"+
		"  Server Id: %q\n"+
		"  Jar-File:  %q\n"+
		"  Running:   %t\n", info.ID, info.JarFile, info.Running())
	return nil
}
