from pathlib import Path
from loguru import logger


def configure_logging(log_dir: Path | None = None) -> None:
    """
    Configure loguru to write structured JSON logs to logs/app.jsonl
    and a human-friendly console logger.
    """
    logger.remove()

    if log_dir is None:
        log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Human-readable console sink
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level="INFO",
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    # JSON structured log sink
    json_path = log_dir / "app.jsonl"
    logger.add(
        str(json_path),
        level="DEBUG",
        enqueue=True,
        rotation="10 MB",
        retention=10,
        compression="zip",
        serialize=True,  # JSON lines
    )


def get_logger():
    return logger