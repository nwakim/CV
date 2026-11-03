# CV repo — notes for Claude

## Syncing from the Claude Doc ("sync my CV")

The CV content is edited in a Claude Doc: https://claude.ai/artifact/2ijEWjFVbARZ3mZXW13mi8
(doc id `0deca904-8cdf-403b-be07-d12fafd4ce71`). The `cv_contents/*.tex` files are generated from it.

1. Pull `main`. Check `git log -- cv_contents/` for commits made since the last
   "Sync CV from Claude Doc" commit; if anyone edited the .tex files directly, show the
   user those changes and ask before overwriting them.
2. Export the doc's tab as Markdown (Claude Docs `export`, format `markdown`), decode it, and
   save it to a scratch file (not in the repo).
3. Run `python3 scripts/doc_to_tex.py <that file>` from the repo root. It rewrites
   `cv_contents/*.tex`; on an error (unknown section, wrong table columns, stray text) fix the
   mapping in `SECTIONS` or ask the user — never hand-edit the .tex to work around it.
4. Show the user `git diff -- cv_contents/` in plain words and wait for their OK.
5. Commit as "Sync CV from Claude Doc" and push. GitHub Actions builds
   `cv/NWakim_CV_YYYY-MM-DD.pdf`; check the run succeeded and the PDF reflects the change.

A new section in the doc needs a new entry in `SECTIONS` in `scripts/doc_to_tex.py`, a new
`cv_contents/<name>.tex`, and an `\input` line in `cv.Rmd`.

Header (name, title, contact), fonts and layout live in `cv.Rmd` and `preamble.tex`, not the doc.
