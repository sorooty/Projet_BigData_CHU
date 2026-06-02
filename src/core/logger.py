import logging


def configure_logging() -> None:
    # Format lisible en local et en logs CI.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
