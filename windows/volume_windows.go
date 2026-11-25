package main

import (
	"fmt"
	"os"
	"syscall"
	"unsafe"
)

var kernel = syscall.NewLazyDLL("kernel32.dll")

func verifyVolume(root string) error {
	path, err := syscall.UTF16PtrFromString(root)
	if err != nil {
		return err
	}
	fsName := make([]uint16, 32)
	status, _, callErr := kernel.NewProc("GetVolumeInformationW").Call(
		uintptr(unsafe.Pointer(path)), 0, 0, 0, 0, 0,
		uintptr(unsafe.Pointer(&fsName[0])), uintptr(len(fsName)),
	)
	if status == 0 {
		return fmt.Errorf("cannot inspect %s: %w", root, callErr)
	}
	if syscall.UTF16ToString(fsName) != "FAT32" {
		return fmt.Errorf("%s must be an existing FAT32 volume", root)
	}
	return nil
}

func isReparsePoint(info os.FileInfo) bool {
	attributes, ok := info.Sys().(*syscall.Win32FileAttributeData)
	return !ok || attributes.FileAttributes&syscall.FILE_ATTRIBUTE_REPARSE_POINT != 0
}
