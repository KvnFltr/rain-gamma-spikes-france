"""Command-line entry point for the Rain & Dust Spikes dashboard project.

Running ``python main.py`` without arguments launches the Dash dashboard so that
it complies with the project specification. Additional sub-commands are
available to orchestrate the data ingestion and cleaning pipeline from the same
interface.
"""

from __future__ import annotations

import argparse
import logging
from typing import Callable

from src.app import create_app
from src.utils.clean_data import clean_all_data
from src.utils.get_data import get_all_data

_LOGGER = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Configure a basic logging setup for CLI feedback."""

    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )


def _run_dashboard(debug: bool = False, host: str = "127.0.0.1", port: int = 8050) -> None:
    """Instantiate and run the Dash dashboard server."""

    app = create_app()
    _LOGGER.info("Starting Dash server on http://%s:%s", host, port)
    app.run_server(debug=debug, host=host, port=port)


def _download_data() -> None:
    """Download the raw datasets into ``data/raw``."""

    _LOGGER.info("Fetching all configured datasets…")
    get_all_data()
    _LOGGER.info("Raw data download complete")


def _clean_data() -> None:
    """Clean the raw datasets and persist results into ``data/cleaned``."""

    _LOGGER.info("Starting data cleaning pipeline…")
<<<<<<< HEAD
    clean_all_data()
    _LOGGER.info("Cleaned datasets available in data/cleaned")


def _build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Rain & Dust Spikes dashboard tooling",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("dashboard", "download", "clean"),
        default="dashboard",
        help="Which action to execute. Defaults to launching the dashboard.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run the Dash development server in debug mode.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Hostname or IP address used by the Dash server (dashboard mode only).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port used by the Dash server (dashboard mode only).",
    )
    return parser


def _dispatch(command: str, **kwargs: object) -> None:
    """Execute the selected command from :func:`_build_parser`."""

    actions: dict[str, Callable[..., None]] = {
        "dashboard": lambda: _run_dashboard(
            debug=bool(kwargs.get("debug")),
            host=str(kwargs.get("host")),
            port=int(kwargs.get("port")),
        ),
        "download": _download_data,
        "clean": _clean_data,
    }
    actions[command]()


def main() -> None:
    """Parse CLI arguments and execute the requested command."""

    _configure_logging()
    parser = _build_parser()
    args = parser.parse_args()
    _dispatch(
        command=str(args.command),
        debug=args.debug,
        host=args.host,
        port=args.port,
    )

    '''
    print("=== Start downloading data ===")
    get_all_data()
    print("=== Data download complete ===")
    
    print("=== Start cleaning up data ===")
    clean_all_data()
    print("=== Data cleaning complete ===")
    '''


=======
    clean_all_data()
    _LOGGER.info("Cleaned datasets available in data/cleaned")


def _build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Rain & Dust Spikes dashboard tooling",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("dashboard", "download", "clean"),
        default="dashboard",
        help="Which action to execute. Defaults to launching the dashboard.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run the Dash development server in debug mode.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Hostname or IP address used by the Dash server (dashboard mode only).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port used by the Dash server (dashboard mode only).",
    )
    return parser


def _dispatch(command: str, **kwargs: object) -> None:
    """Execute the selected command from :func:`_build_parser`."""

    actions: dict[str, Callable[..., None]] = {
        "dashboard": lambda: _run_dashboard(
            debug=bool(kwargs.get("debug")),
            host=str(kwargs.get("host")),
            port=int(kwargs.get("port")),
        ),
        "download": _download_data,
        "clean": _clean_data,
    }
    actions[command]()


def main() -> None:
    """Parse CLI arguments and execute the requested command."""

    _configure_logging()
    parser = _build_parser()
    args = parser.parse_args()
    _dispatch(
        command=str(args.command),
        debug=args.debug,
        host=args.host,
        port=args.port,
    )

>>>>>>> 103a673174c26f612788fe848d1be4ea8f77ddba

if __name__ == "__main__":
    main()
