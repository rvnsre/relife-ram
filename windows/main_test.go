package main

import (
	"archive/zip"
	"crypto/sha256"
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func samplePayload(t *testing.T, names []string) (string, string) {
	t.Helper()
	path := filepath.Join(t.TempDir(), "payload.zip")
	file, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	archive := zip.NewWriter(file)
	for _, name := range names {
		item, err := archive.Create(name)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := item.Write([]byte(name)); err != nil {
			t.Fatal(err)
		}
	}
	if err := archive.Close(); err != nil {
		t.Fatal(err)
	}
	if err := file.Close(); err != nil {
		t.Fatal(err)
	}
	bytes, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return path, fmt.Sprintf("%x", sha256.Sum256(bytes))
}

func TestStageRecovery(t *testing.T) {
	root := t.TempDir()
	path, hash := samplePayload(t, payloadFiles)
	if err := install(root, path, hash); err != nil {
		t.Fatal(err)
	}
	if err := install(root, path, hash); err == nil {
		t.Fatal("existing installation should be preserved")
	}
	efi := filepath.Join(root, "EFI")
	out := filepath.Join(efi, "ReLife")
	unrelated := filepath.Join(out, "keep.txt")
	if err := os.WriteFile(unrelated, []byte("keep"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := uninstall(root); err == nil {
		t.Fatal("recovery should preserve unknown files")
	}
	if _, err := os.Stat(filepath.Join(out, "ReLife.efi")); err != nil {
		t.Fatal(err)
	}
	if err := os.Remove(unrelated); err != nil {
		t.Fatal(err)
	}
	if err := uninstall(root); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Fatalf("staged path still exists or cannot be inspected: %v", err)
	}
	if _, err := os.Stat(efi); err != nil {
		t.Fatal(err)
	}
}

func TestRejectUntrustedPayload(t *testing.T) {
	root := t.TempDir()
	path, hash := samplePayload(t, []string{"../outside", "live/vmlinuz", "live/initrd.img", "live/filesystem.squashfs"})
	if err := install(root, path, hash); err == nil {
		t.Fatal("unexpected archive entry accepted")
	}
	path, _ = samplePayload(t, payloadFiles)
	if err := install(root, path, hash); err == nil {
		t.Fatal("checksum mismatch accepted")
	}
	if _, err := os.Stat(filepath.Join(root, "EFI")); !os.IsNotExist(err) {
		t.Fatalf("installer touched volume for invalid payload: %v", err)
	}
}

func TestWindowsFAT32Volume(t *testing.T) {
	volume := os.Getenv("RELIFE_TEST_VOLUME")
	if volume == "" {
		t.Skip("requires the CI-created, disposable FAT32 volume")
	}
	path, hash := samplePayload(t, payloadFiles)
	if err := run(volume, path, hash, false, true); err != nil {
		t.Fatal(err)
	}
	if err := run(volume, "", "", true, true); err != nil {
		t.Fatal(err)
	}
}
