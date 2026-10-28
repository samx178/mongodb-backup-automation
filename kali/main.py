"""Kali - Universal MongoDB Backup Automation."""

import logging


def configure_logging() -> None:
    """Configure the application's basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    """Start the Kali application."""
    configure_logging()

    logger = logging.getLogger("kali")
    logger.info("Kali MongoDB Backup Automation starting.")
    logger.info("Application foundation initialized successfully.")


if __name__ == "__main__":
    main()