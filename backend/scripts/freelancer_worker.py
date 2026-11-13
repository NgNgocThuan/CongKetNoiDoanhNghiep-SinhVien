"""Run once or continuously; uses DATABASE_URL, never migrates or seeds."""

import argparse
import time

from app.core.database import SessionLocal
from app.services.freelancer_worker import run_once


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=3)
    args = parser.parse_args()
    while True:
        with SessionLocal() as db:
            run_once(db)
        if args.once:
            break
        time.sleep(max(0.2, args.interval))


if __name__ == "__main__":
    main()
