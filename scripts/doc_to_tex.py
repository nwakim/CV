#!/usr/bin/env python3
"""Convert the "Nicky Wakim — CV" Claude Doc (exported as Markdown) into the
section files in cv_contents/.

Usage:
    python3 scripts/doc_to_tex.py path/to/exported_doc.md [--out cv_contents]

The doc is laid out as one "## Section" per .tex file (optionally split into
"### Subsection" groups), each holding a table, a bullet list or a numbered
list. SECTIONS below says which file each section goes to and how it is
rendered. Inline Markdown is converted to LaTeX: **bold** -> \\textbf,
*italic* -> \\textit, [text](url) -> \\href, "quotes" -> ``quotes'', and
LaTeX special characters (& % $ # _ ...) are escaped.

A "## Section" that is not listed (other than the "How to use" notes) stops the
script with an error, so a new section is never silently dropped.
"""

import argparse
import re
import sys
from pathlib import Path

# heading in the doc -> (file name in cv_contents/, renderer, expected table columns)
SECTIONS = {
    "Education": ("education", "educ", ["Degree", "Institution", "Location", "Dates"]),
    "Areas of Scholarly Interest": ("research_interest", "itemize", None),
    "Professional Experience": ("Academic_positions", "experience",
                                ["Dates", "Position", "Organization", "Advisors"]),
    "Honors and Awards": ("honors", "tight", ["Dates", "Entry"]),
    "Publications": ("writing", "enumerate", None),
    "Presentations": ("presentation", "enumerate", None),
    "Grants and Contracts": ("Funding", "grants", ["Dates", "Grant", "Role", "Description"]),
    "Professional Service": ("Service", "tight", ["Dates", "Entry"]),
    "Professional Memberships": ("Professional_memberships", "tight", ["Dates", "Organization"]),
    "Teaching": ("Teaching_experience", "tight", ["Dates", "Entry"]),
    "Mentorship": ("Mentorship", "mentor", ["Dates", "Mentee", "Details", "Role"]),
    "Additional Training": ("Additional_training", "training", ["Dates", "Training", "Provider"]),
}
SKIP_SECTIONS = {"How to use this doc"}

TEX_ESCAPES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


class DocError(Exception):
    pass


# ---------------------------------------------------------------- inline text

def escape_plain(text):
    out = []
    i = 0
    while i < len(text):
        c = text[i]
        # Markdown backslash-escape (\* \_ \& ...) -> the literal character
        if c == "\\" and i + 1 < len(text) and not text[i + 1].isalnum():
            out.append(TEX_ESCAPES.get(text[i + 1], text[i + 1]))
            i += 2
            continue
        out.append(TEX_ESCAPES.get(c, c))
        i += 1
    return "".join(out)


def escape_url(url):
    return url.replace("\\", "").replace("%", r"\%").replace("#", r"\#")


INLINE = re.compile(
    r"\[(?P<ltext>[^\]]+)\]\((?P<url>[^)\s]+)\)"   # [text](url)
    r"|\*\*(?P<bold>.+?)\*\*"                    # **bold**
    r"|__(?P<bold2>.+?)__"                       # __bold__
    r"|(?<![\w*])\*(?P<ital>[^*]+?)\*(?!\*)"     # *italic*
    r"|(?<!\w)_(?P<ital2>[^_]+?)_(?!\w)"         # _italic_
    r"|`(?P<code>[^`]+)`"                        # `code` -> plain text
)


def inline(text):
    """Markdown inline text -> LaTeX (quotes are handled by tex())."""
    out = []
    pos = 0
    for m in INLINE.finditer(text):
        out.append(escape_plain(text[pos:m.start()]))
        if m.group("ltext") is not None:
            out.append(r"\href{%s}{%s}" % (escape_url(m.group("url")), inline(m.group("ltext"))))
        elif m.group("bold") is not None or m.group("bold2") is not None:
            out.append(r"\textbf{%s}" % inline(m.group("bold") or m.group("bold2")))
        elif m.group("ital") is not None or m.group("ital2") is not None:
            out.append(r"\textit{%s}" % inline(m.group("ital") or m.group("ital2")))
        else:
            out.append(escape_plain(m.group("code")))
        pos = m.end()
    out.append(escape_plain(text[pos:]))
    return "".join(out)


def tex(text):
    """One cell / list item of Markdown -> LaTeX, with ``proper'' quotes."""
    text = text.strip().replace("“", '"').replace("”", '"')
    result = inline(text)
    parts = result.split('"')
    if len(parts) > 1:
        result = parts[0]
        for n, part in enumerate(parts[1:]):
            result += ("``" if n % 2 == 0 else "''") + part
    return result


# ---------------------------------------------------------------- doc parsing

def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    return [c.strip().replace("\\|", "|") for c in cells]


def parse_blocks(lines):
    """Lines of one (sub)section -> list of ("table", header, rows) | ("list", kind, items)."""
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            header = split_row(line)
            i += 1
            if i < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i]):
                i += 1
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            blocks.append(("table", header, rows))
            continue
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if m:
            kind = "ordered" if m.group(2)[0].isdigit() else "bullet"
            items = []
            while i < len(lines):
                m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if m:
                    items.append(m.group(3))
                elif lines[i].strip() and items:
                    items[-1] += " " + lines[i].strip()   # wrapped continuation line
                else:
                    break
                i += 1
            blocks.append(("list", kind, items))
            continue
        if line.strip():
            raise DocError("unexpected text (not a table or list): %r" % line.strip()[:80])
        i += 1
    return blocks


def parse_doc(md):
    """Markdown -> {section: [(subsection or None, blocks)]} in doc order."""
    sections = {}
    current = None
    sub = None
    buf = []

    def flush():
        if current is not None and current not in SKIP_SECTIONS:
            blocks = parse_blocks(buf)
            if blocks or sub is not None:
                sections[current].append((sub, blocks))

    for line in md.splitlines():
        h2 = re.match(r"^##\s+(.*?)\s*#*\s*$", line)
        h3 = re.match(r"^###\s+(.*?)\s*#*\s*$", line)
        if h3:
            flush()
            sub, buf = h3.group(1), []
        elif h2:
            flush()
            current, sub, buf = h2.group(1).strip(), None, []
            if current in SKIP_SECTIONS:
                continue
            if current not in SECTIONS:
                raise DocError("unknown section %r — add it to SECTIONS in %s"
                               % (current, Path(__file__).name))
            if current in sections:
                raise DocError("section %r appears twice" % current)
            sections[current] = []
        elif current is not None:
            buf.append(line)
    flush()
    return sections


# ---------------------------------------------------------------- rendering

def rows_as_dicts(section, sub, block, columns):
    kind, header, rows = block
    if kind != "table":
        raise DocError("%s / %s: expected a table" % (section, sub or "-"))
    if header != columns:
        raise DocError("%s / %s: table columns are %s, expected %s"
                       % (section, sub or "-", header, columns))
    out = []
    for r in rows:
        if not any(c.strip() for c in r):
            continue  # blank row
        r = (r + [""] * len(columns))[:len(columns)]
        out.append(dict(zip(columns, r)))
    return out


def render_entry(renderer, row):
    d = {k: tex(v) for k, v in row.items()}
    if renderer == "educ":
        return r"\cveduc{%s}{%s}{%s}{%s}" % (d["Degree"], d["Institution"], d["Location"], d["Dates"])
    if renderer == "tight":
        entry = d.get("Entry", d.get("Organization"))
        return r"\cvrowtight{%s}{%s}" % (d["Dates"], entry)
    if renderer == "experience":
        body = r"\textbf{%s} \newline %s" % (d["Position"], d["Organization"])
        if d["Advisors"]:
            body += r" \newline Advisors: %s" % d["Advisors"]
        return r"\cvrow{%s}{%s}" % (d["Dates"], body)
    if renderer == "grants":
        body = r"\textbf{%s}" % d["Grant"]
        tail = " ".join(x for x in [("Role: " + d["Role"]) if d["Role"] else "", d["Description"]] if x)
        if tail:
            body += r" \newline " + tail
        return r"\cvrow{%s}{%s}" % (d["Dates"], body)
    if renderer == "mentor":
        body = r"\textbf{\textmd{%s}}" % d["Mentee"]
        if d["Details"]:
            body += r" \newline " + d["Details"]
        if d["Role"]:
            body += r" \newline \textbf{Role:} " + d["Role"]
        return r"\cvrow{%s}{%s}" % (d["Dates"], body)
    if renderer == "training":
        body = r"\textbf{%s}" % d["Training"]
        if d["Provider"]:
            body += r" \newline " + d["Provider"]
        return r"\cvrowtight{%s}{%s}" % (d["Dates"], body)
    raise AssertionError(renderer)


def render_section(name, groups):
    fname, renderer, columns = SECTIONS[name]
    out = [r"\cvsection{%s}" % tex(name), ""]
    for sub, blocks in groups:
        if sub is not None:
            out += [r"\cvsubsection{%s}" % tex(sub), ""]
        for block in blocks:
            if renderer in ("itemize", "enumerate"):
                if block[0] != "list":
                    raise DocError("%s / %s: expected a list" % (name, sub or "-"))
                env = "itemize" if renderer == "itemize" else "enumerate"
                out.append(r"\begin{%s}" % env)
                out += [r"\item " + tex(item) for item in block[2]]
                out.append(r"\end{%s}" % env)
            else:
                for row in rows_as_dicts(name, sub, block, columns):
                    out.append(render_entry(renderer, row))
            out.append("")
    return fname, "\n".join(out).rstrip("\n") + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("markdown", help="Markdown export of the CV doc")
    ap.add_argument("--out", default="cv_contents", help="output folder (default: cv_contents)")
    args = ap.parse_args()

    md = Path(args.markdown).read_text(encoding="utf-8")
    try:
        sections = parse_doc(md)
        missing = [s for s in SECTIONS if s not in sections]
        if missing:
            raise DocError("sections missing from the doc: %s" % ", ".join(missing))
        outputs = [render_section(name, groups) for name, groups in sections.items()]
    except DocError as e:
        sys.exit("doc_to_tex: " + str(e))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for fname, text in outputs:
        (out / (fname + ".tex")).write_text(text, encoding="utf-8")
        print("wrote", out / (fname + ".tex"))


if __name__ == "__main__":
    main()
