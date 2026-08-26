from __future__ import annotations

import argparse
import os
import sys

from typing import Optional

from .document.pdf_reader import read_pdf_to_document
from .document.pdf_writer import write_document_to_pdf


def _error(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)


def roundtrip_command(input_path: str, output_path: str) -> int:
    # validate input
    if not os.path.exists(input_path):
        _error(f"Input file does not exist: {input_path}")
        return 2
    if not os.path.isfile(input_path):
        _error(f"Input path is not a file: {input_path}")
        return 2

    out_dir = os.path.dirname(output_path) or os.getcwd()
    if out_dir and not os.path.exists(out_dir):
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as exc:
            _error(f"Cannot create output directory {out_dir}: {exc}")
            return 3

    try:
        doc = read_pdf_to_document(input_path)
    except Exception as exc:
        _error(f"Failed to read PDF: {exc}")
        return 4

    try:
        write_document_to_pdf(doc, output_path)
    except Exception as exc:
        _error(f"Failed to write PDF: {exc}")
        return 5

    print(f"Wrote: {output_path}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="odt")
    sub = parser.add_subparsers(dest="command")

    rp = sub.add_parser("roundtrip", help="Read PDF into Document and write back")
    rp.add_argument("input", help="Input PDF path")
    rp.add_argument("--output", "-o", required=True, help="Output PDF path")

    args = parser.parse_args(argv)
    if args.command == "roundtrip":
        return roundtrip_command(args.input, args.output)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
