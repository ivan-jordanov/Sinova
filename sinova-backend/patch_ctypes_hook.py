import os
import sys
import ctypes
import ctypes.util

if sys.platform.startswith("linux") and hasattr(sys, "_MEIPASS"):
    _orig_find_library = ctypes.util.find_library

    def _find_library(name):
        if name and name.startswith("tomo-"):
            path = os.path.join(sys._MEIPASS, f"lib{name}.so")
            if os.path.isfile(path):
                try:
                    import _ctypes
                    _ctypes.dlopen(path)  # raw dlerror, bypasses PyInstaller's wrapper
                except OSError as e:
                    sys.stderr.write(f"[tomo hook] raw dlopen error for {path}: {e}\n")
                except Exception as e:
                    sys.stderr.write(f"[tomo hook] unexpected error for {path}: {e!r}\n")
                return path
        return _orig_find_library(name)

    ctypes.util.find_library = _find_library