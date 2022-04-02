package util

import (
	"errors"
	"os"
	"path"
	"strings"
)

var (
	ErrDataFileNotExisting = errors.New("datafile is not existing")
)

func getDataFilePath() (string, error) {
	uhd, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}

	return path.Join(uhd, ".mcsrvrc"), nil
}

func GetAllServerPaths() ([]string, error) {
	dataFile, err := getDataFilePath()
	if err != nil {
		return nil, err
	}

	if !IsFile(dataFile) {
		return nil, ErrDataFileNotExisting
	}

	data, err := os.ReadFile(dataFile)

	return strings.Split(string(data), "\n"), nil
}

func SaveServerPath(p string) error {
	existing, err := GetAllServerPaths()
	if err != nil {
		return err
	}

	// check if server is already saved
	for _, srv := range existing {
		if srv == p {
			return nil
		}
	}

	dataFile, err := getDataFilePath()
	if err != nil {
		return err
	}

	f, err := os.OpenFile(dataFile, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0600)
	if err != nil {
		return err
	}

	defer f.Close()

	_, err = f.WriteString(p + "\n")
	return err
}
