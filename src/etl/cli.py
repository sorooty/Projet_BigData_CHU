import argparse

from src.core.db import get_engine
from src.core.logger import configure_logging
from src.etl.jobs.pilot_soins import PilotSoinsJob


def main() -> None:
    # Lanceur unique pour tous les jobs.
    # On ajoute les prochains jobs dans choices.
    parser = argparse.ArgumentParser(description="Lanceur de jobs ETL CHU")
    parser.add_argument(
        "--job",
        required=True,
        choices=["pilot_soins"],
        help="Nom du job ETL à exécuter.",
    )
    args = parser.parse_args()

    configure_logging()
    engine = get_engine()

    if args.job == "pilot_soins":
        PilotSoinsJob(engine).run()


if __name__ == "__main__":
    main()
