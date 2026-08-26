from __future__ import annotations

import os
import subprocess
import sys

import fitz

from odt.document.pdf_reader import read_pdf_to_document


def _make_sample_pdf(path: str) -> None:
    d = fitz.open()
    p = d.new_page(width=250, height=180)
    p.insert_text((30, 40), "CLI Roundtrip", fontsize=13, fontname="Times-Roman")
    d.save(path)


def test_cli_roundtrip_success(tmp_path):
    in_pdf = tmp_path / "in.pdf"
    out_pdf = tmp_path / "out.pdf"
    _make_sample_pdf(str(in_pdf))

    # invoke the CLI via the current Python interpreter
    env = os.environ.copy()
    # Ensure local `src` is on PYTHONPATH so `-m odt.cli` can import the package
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    res = subprocess.run([sys.executable, "-m", "odt.cli", "roundtrip", str(in_pdf), "--output", str(out_pdf)], capture_output=True, text=True, env=env)
    assert res.returncode == 0, f"CLI failed: {res.stderr}"
    assert out_pdf.exists()

    # verify page count and text
    doc_in = read_pdf_to_document(str(in_pdf))
    doc_out = read_pdf_to_document(str(out_pdf))
    assert len(doc_in.pages) == len(doc_out.pages)
    texts_in = "\n".join([el.text for el in doc_in.pages[0].elements if hasattr(el, "text")])
    texts_out = "\n".join([el.text for el in doc_out.pages[0].elements if hasattr(el, "text")])
    assert "CLI Roundtrip" in texts_in
    assert "CLI Roundtrip" in texts_out


def test_cli_input_validation_fails(tmp_path):
    # non-existent input
    out_pdf = tmp_path / "out.pdf"
    env = os.environ.copy()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    res = subprocess.run([sys.executable, "-m", "odt.cli", "roundtrip", str(tmp_path / "nope.pdf"), "--output", str(out_pdf)], capture_output=True, text=True, env=env)
    assert res.returncode != 0
    assert "does not exist" in res.stderr
