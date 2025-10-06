import sys
import traceback

try:
    # Defer heavy imports so we can catch and report import-time errors
    from autoclick_pro.app import main  # type: ignore
except Exception as e:
    # Best-effort error reporting for import failures
    try:
        from autoclick_pro.logging.logger import configure_logging, get_logger  # type: ignore
        configure_logging()
        get_logger().exception("fatal_import_error")
    except Exception:
        # If logging itself fails, print to stderr
        traceback.print_exc()
    # Keep console open when double-clicked on Windows
    if sys.platform.startswith("win"):
        print("Import failed. See traceback/logs above.")
        try:
            input("Press Enter to exit...")
        except Exception:
            pass
    sys.exit(1)


def _run() -> int:
    try:
        main()
        return 0
    except SystemExit as se:
        # Respect explicit sys.exit codes from Qt loop
        return int(se.code) if se.code is not None else 0
    except Exception:
        # Configure logging (idempotent) and record full traceback
        try:
            from autoclick_pro.logging.logger import configure_logging, get_logger  # type: ignore
            configure_logging()
            get_logger().exception("fatal_runtime_error")
        except Exception:
            traceback.print_exc()
        # Keep console visible when launched by double-click on Windows
        if sys.platform.startswith("win"):
            print("A fatal error occurred. See traceback/logs above.")
            try:
                input("Press Enter to exit...")
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(_run())