from __future__ import annotations

import argparse
from pathlib import Path

from core.monitoring_api import serve


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the MetaCode Observatory dashboard and API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8770, type=int)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    server = serve(root, host=args.host, port=args.port)
    print(f"MetaCode Observatory API: http://{args.host}:{args.port}/dashboard/")
    print(f"API status: http://{args.host}:{args.port}/api/status")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping MetaCode Observatory API.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
