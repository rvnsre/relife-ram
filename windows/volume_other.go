//go:build !windows

package main

import (
	"errors"
	"os"
)

func verifyVolume(string) error {
	return errors.New("the volume setup command requires Windows")
}

func isReparsePoint(info os.FileInfo) bool {
	return info.Mode()&os.ModeSymlink != 0
}
