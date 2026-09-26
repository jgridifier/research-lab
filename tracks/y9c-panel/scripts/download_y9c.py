"""CLI for the NIC downloader."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from y9c.download import main

if __name__ == '__main__':
    raise SystemExit(main())
