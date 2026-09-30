use std::sync::{Arc, Mutex};
use tauri_plugin_shell::process::CommandEvent;
use tauri_plugin_shell::ShellExt;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let sidecar_pid = Arc::new(Mutex::new(None::<u32>));
    let sidecar_pid_clone = sidecar_pid.clone();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(move |app| {
            let sidecar_command = app.shell().sidecar("sinova-backend");

            match sidecar_command {
                Ok(cmd) => {
                    let (mut rx, child) = cmd.spawn().expect("Failed to spawn backend sidecar");
                    
                    // Save sidecar PID for teardown on exit
                    if let Ok(mut lock) = sidecar_pid_clone.lock() {
                        *lock = Some(child.pid());
                    }

                    tauri::async_runtime::spawn(async move {
                        while let Some(event) = rx.recv().await {
                            match event {
                                CommandEvent::Stdout(line) => {
                                    println!("[Backend STDOUT] {}", String::from_utf8_lossy(&line));
                                }
                                CommandEvent::Stderr(line) => {
                                    eprintln!("[Backend STDERR] {}", String::from_utf8_lossy(&line));
                                }
                                CommandEvent::Error(err) => {
                                    eprintln!("[Backend ERROR] {}", err);
                                }
                                CommandEvent::Terminated(payload) => {
                                    println!("[Backend Terminated] Exit code: {:?}", payload.code);
                                }
                                _ => {}
                            }
                        }
                    });
                }
                Err(err) => {
                    eprintln!("Failed to initialize sidecar command: {}", err);
                }
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(move |_app_handle, event| {
            if let tauri::RunEvent::Exit = event {
                if let Ok(lock) = sidecar_pid.lock() {
                    if let Some(pid) = *lock {
                        #[cfg(target_os = "windows")]
                        {
                            let _ = std::process::Command::new("taskkill")
                                .args(["/PID", &pid.to_string(), "/T", "/F"])
                                .output();
                        }
                    }
                }
            }
        });
}