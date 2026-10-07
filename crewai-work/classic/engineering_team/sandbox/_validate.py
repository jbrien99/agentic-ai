"""Validation script for the Gradio app construction."""
from __future__ import annotations

import app


def main() -> None:
    demo = app.build_app()
    assert demo is not None
    print(type(demo).__name__)
    print("OK")


if __name__ == "__main__":
    main()
