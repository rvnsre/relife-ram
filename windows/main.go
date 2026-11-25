package main

import (
	"archive/zip"
	"crypto/sha256"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

const marker = "ReLife USB-free boot media v1\n"

var payloadFiles = []string{"ReLife.efi", "live/vmlinuz", "live/initrd.img", "live/filesystem.squashfs"}
var driveLetter = regexp.MustCompile(`^[A-Za-z]:[\\/]?$`)
var sha256Text = regexp.MustCompile(`^[0-9a-fA-F]{64}$`)

func main() {
	volume := flag.String("volume", "", "drive letter of a dedicated existing FAT32 volume, such as R:")
	payload := flag.String("payload", "", "path to the ReLife Windows payload ZIP")
	digest := flag.String("sha256", "", "SHA-256 of the payload from SHA256SUMS")
	remove := flag.Bool("remove", false, "remove the staged ReLife boot files")
	confirm := flag.Bool("confirm", false, "confirm changes to EFI\\ReLife on the selected volume")
	flag.Parse()
	if err := run(*volume, *payload, *digest, *remove, *confirm); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(volume, payload, digest string, remove, confirm bool) error {
	if !driveLetter.MatchString(volume) || !confirm {
		return errors.New("Provide a dedicated FAT32 drive with -volume R: and confirm with -confirm. Use -help for options.")
	}
	root := strings.ToUpper(volume[:2]) + `\`
	if strings.EqualFold(strings.TrimRight(root, `\`), os.Getenv("SystemDrive")) {
		return errors.New("Select a separate FAT32 volume from the Windows system drive.")
	}
	if err := verifyVolume(root); err != nil {
		return err
	}
	if remove {
		if err := uninstall(root); err != nil {
			return err
		}
		fmt.Println("ReLife boot files removed.")
		return nil
	}
	if payload == "" || !sha256Text.MatchString(digest) {
		return errors.New("Provide -payload and its 64-digit SHA-256 from SHA256SUMS.")
	}
	if err := install(root, payload, strings.ToLower(digest)); err != nil {
		return err
	}
	fmt.Printf("Staged on %s. In UEFI's Boot from File menu, select EFI\\ReLife\\ReLife.efi.\n", root)
	return nil
}

func verifyDirectory(path string) error {
	info, err := os.Lstat(path)
	if err != nil {
		return err
	}
	if !info.IsDir() || isReparsePoint(info) {
		return fmt.Errorf("expected a regular directory at %s", path)
	}
	return nil
}

func install(root, payload, wantHash string) error {
	file, err := os.Open(payload)
	if err != nil {
		return err
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() || info.Size() < 1 || info.Size() > 1_500_000_000 {
		return errors.New("unexpected payload file type or size")
	}
	// Copy and hash once. The verified bytes in the private temporary file are
	// the same bytes subsequently passed to the ZIP reader.
	snapshot, err := os.CreateTemp("", "relife-verified-*.zip")
	if err != nil {
		return err
	}
	defer os.Remove(snapshot.Name())
	defer snapshot.Close()
	hash := sha256.New()
	n, err := io.Copy(io.MultiWriter(hash, snapshot), io.LimitReader(file, 1_500_000_001))
	if err != nil {
		return err
	}
	if n != info.Size() || fmt.Sprintf("%x", hash.Sum(nil)) != wantHash {
		return errors.New("payload SHA-256 mismatch")
	}
	reader, err := zip.NewReader(snapshot, n)
	if err != nil {
		return err
	}
	entries, err := validatePayload(reader.File)
	if err != nil {
		return err
	}
	efi := filepath.Join(root, "EFI")
	destination := filepath.Join(efi, "ReLife")
	if err := os.Mkdir(efi, 0755); err != nil && !os.IsExist(err) {
		return err
	}
	if err := verifyDirectory(efi); err != nil {
		return err
	}
	if _, err := os.Lstat(destination); !os.IsNotExist(err) {
		if err != nil {
			return err
		}
		return errors.New("EFI\\ReLife already exists. Remove a prior ReLife installation before updating.")
	}
	stage, err := os.MkdirTemp(efi, "ReLife-stage-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(stage)
	if err = os.Mkdir(filepath.Join(stage, "live"), 0755); err != nil {
		return err
	}
	for _, name := range payloadFiles {
		if err := extract(filepath.Join(stage, filepath.FromSlash(name)), entries[name]); err != nil {
			return err
		}
	}
	if err := os.WriteFile(filepath.Join(stage, "relife-media"), []byte(marker), 0644); err != nil {
		return err
	}
	return os.Rename(stage, destination)
}

func validatePayload(files []*zip.File) (map[string]*zip.File, error) {
	if len(files) != len(payloadFiles) {
		return nil, errors.New("unexpected ZIP contents")
	}
	limits := map[string]uint64{
		"ReLife.efi": 32_000_000, "live/vmlinuz": 64_000_000,
		"live/initrd.img": 256_000_000, "live/filesystem.squashfs": 1_000_000_000,
	}
	entries := make(map[string]*zip.File)
	for _, file := range files {
		limit, known := limits[file.Name]
		if !known || !file.Mode().IsRegular() || entries[file.Name] != nil ||
			file.UncompressedSize64 == 0 || file.UncompressedSize64 > limit {
			return nil, fmt.Errorf("invalid ZIP entry %q", file.Name)
		}
		entries[file.Name] = file
	}
	return entries, nil
}

func extract(path string, file *zip.File) error {
	source, err := file.Open()
	if err != nil {
		return err
	}
	defer source.Close()
	target, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		return err
	}
	expected := int64(file.UncompressedSize64)
	n, copyErr := io.Copy(target, io.LimitReader(source, expected+1))
	closeErr := target.Close()
	if err := errors.Join(copyErr, closeErr); err != nil {
		return err
	}
	if n != expected {
		return errors.New("unexpected payload entry length")
	}
	return nil
}

func uninstall(root string) error {
	efi := filepath.Join(root, "EFI")
	path := filepath.Join(efi, "ReLife")
	for _, dir := range []string{efi, path, filepath.Join(path, "live")} {
		if err := verifyDirectory(dir); err != nil {
			return err
		}
	}
	ident := filepath.Join(path, "relife-media")
	info, err := os.Lstat(ident)
	if err != nil || !info.Mode().IsRegular() || isReparsePoint(info) || info.Size() != int64(len(marker)) {
		return errors.New("ReLife installation marker missing or invalid")
	}
	data, err := os.ReadFile(ident)
	if err != nil || string(data) != marker {
		return errors.New("ReLife installation marker missing or invalid")
	}

	// Refuse before removing anything if the directory contains unrelated files.
	for _, dir := range []string{path, filepath.Join(path, "live")} {
		entries, err := os.ReadDir(dir)
		if err != nil {
			return err
		}
		for _, entry := range entries {
			relative, err := filepath.Rel(path, filepath.Join(dir, entry.Name()))
			if err != nil {
				return err
			}
			name := filepath.ToSlash(relative)
			switch name {
			case "relife-media", "live":
			default:
				found := false
				for _, allowed := range payloadFiles {
					found = found || name == allowed
				}
				if !found {
					return fmt.Errorf("unexpected file %s; ReLife files were preserved", name)
				}
			}
		}
	}
	for _, name := range payloadFiles {
		if err := os.Remove(filepath.Join(path, filepath.FromSlash(name))); err != nil && !os.IsNotExist(err) {
			return err
		}
	}
	if err := os.Remove(filepath.Join(path, "live")); err != nil && !os.IsNotExist(err) {
		return err
	}
	if err := os.Remove(ident); err != nil {
		return err
	}
	return os.Remove(path)
}
