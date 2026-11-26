"""The e-prescription a patient at home downloads from their status page, as a one-page PDF.

Written by hand (PDF is plain text underneath), so nothing new is installed. It holds only what the
status page shows: the reference, the date and each medicine with how much and how to take it. Never
the diagnosis. It is not yet a prescription a pharmacy can trust: there is no prescriber's name,
registration number or signature, and the page says so.
"""

from __future__ import annotations

import textwrap
import time

NAVY, RED, GREY, INK = "0.043 0.122 0.290", "0.824 0.149 0.188", "0.40 0.43 0.48", "0.10 0.11 0.13"


def _text(s: str) -> str:
    """A PDF string in the built-in fonts' Latin-1, with ( ) and \\ escaped."""
    s = str(s).encode("latin-1", "replace").decode("latin-1")
    return "(" + s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ")"


def pdf(view: dict) -> bytes:
    """`view` is visits.status_view() of a visit that has a prescription."""
    rx, sample = view["prescription"], view.get("sample")
    ops: list[str] = []
    y = 790

    def write(s, size=11, bold=False, colour=INK, x=56):
        ops.append(f"BT {colour} rg /F{2 if bold else 1} {size} Tf {x} {y} Td {_text(s)} Tj ET")

    def rule(width=0.8, colour=GREY):
        ops.append(f"{colour} RG {width} w 56 {y} m 539 {y} l S")

    ops.append(f"{NAVY} rg 0 812 595 30 re f")                        # the navy band, as on every screen
    ops.append(f"{RED} rg 0 808 595 4 re f")
    y = 821; write("Mukoti", 13, True, "1 1 1", 56)
    y = 770; write("E-prescription", 24, True, NAVY)
    if sample:
        write("SAMPLE - NOT A VALID PRESCRIPTION", 11, True, RED, 330)
    y -= 26
    write(f"Reference {rx['number']}", 12, True)
    write(time.strftime("%d %B %Y", time.localtime(rx["date"])), 12, False, INK, 400)
    y -= 14; rule()
    y -= 30
    for i, item in enumerate(rx["items"], 1):
        write(f"{i}.  {item['name']}  -  {item['qty']} {item['unit']}", 13, True)
        for line in textwrap.wrap(item["how"], 80):
            y -= 18; write(line, 11, False, GREY, 76)
        y -= 30
        if y < 160:
            break                                                     # one page: the doctor's list is short
    rule()
    y -= 24; write("Show this at any pharmacy. The pharmacist will check it is valid.", 11)
    y -= 34
    for line in ("Not yet valid at a pharmacy: it has no prescriber's name, registration number or signature.",
                 "Made by Mukoti, a hackathon prototype. No diagnosis is printed: it is given by a person."):
        write(line, 9, False, GREY); y -= 14

    stream = "\n".join(ops).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 6 0 R "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for n, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)
