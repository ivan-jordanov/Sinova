use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

fn kill_lingering_sidecars() {
    #[cfg(target_os = "windows")]
    {
        // Terminate orphaned sidecar processes holding DLL locks before compilation starts
        let _ = Command::new("taskkill")
            .args(["/F", "/IM", "sinova-backend*"])
            .output();
        let _ = Command::new("taskkill")
            .args(["/F", "/IM", "main.exe"])
            .output();
    }
}

fn copy_dir_all(src: impl AsRef<Path>, dst: impl AsRef<Path>) -> std::io::Result<()> {
    fs::create_dir_all(&dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let ty = entry.file_type()?;
        let src_path = entry.path();
        let dst_path = dst.as_ref().join(entry.file_name());

        if ty.is_dir() {
            copy_dir_all(&src_path, &dst_path)?;
        } else {
            // Check file metadata before copying to prevent unnecessary writes to locked files
            let should_copy = match (fs::metadata(&src_path), fs::metadata(&dst_path)) {
                (Ok(src_meta), Ok(dst_meta)) => {
                    src_meta.len() != dst_meta.len()
                        || src_meta.modified().ok() > dst_meta.modified().ok()
                }
                _ => true,
            };

            if should_copy {
                if let Err(err) = fs::copy(&src_path, &dst_path) {
                    eprintln!("cargo:warning=Skipped copying {:?}: {}", src_path, err);
                }
            }
        }
    }
    Ok(())
}

fn main() {
    // 1. Force-kill background processes to release DLL file locks
    kill_lingering_sidecars();

    // 2. Execute standard Tauri build
    tauri_build::build();

    // 3. Incrementally copy _internal into target/debug or target/release
    if let Ok(profile) = env::var("PROFILE") {
        let target_dir = PathBuf::from("target").join(profile);
        let src_internal = PathBuf::from("binaries/_internal");
        let dst_internal = target_dir.join("_internal");

        if src_internal.exists() {
            let _ = copy_dir_all(&src_internal, &dst_internal);
        }
    }
}