# Nicole (Nicky) I. Wakim — CV

📄 **[Download the latest CV (PDF)](cv.pdf)**

`cv.pdf` is rebuilt automatically by GitHub Actions (`.github/workflows/build-cv.yml`) whenever `cv.Rmd`, `preamble.tex`, `fonts/`, or anything in `cv_contents/` changes on `main` — just edit a section file, commit, and push. You can also trigger a rebuild by hand from the repo's **Actions** tab → *Build CV PDF* → *Run workflow*.

Source for my academic CV, written in R Markdown + LaTeX. A main file pulls in individual section files with `\input`, so sections can be mixed and matched into different CV/resume variants.

**Note on fidelity:** this is a close visual match, not a pixel-perfect clone. It reproduces the two-column date/content layout, section headers with trailing rules, contact icons, real bullet points, and numbered publications/presentations from your original.

## What's in this folder

```
cv.Rmd                   ← main CV (knit to produce cv.pdf) — pulls in every section via \input
resume_short_example.Rmd ← example of a trimmed-down variant (Education, Experience, Teaching only)
preamble.tex             ← LaTeX styling (fonts, icons, section rule, two-column row commands, footer)
fonts/                   ← Roboto + FontAwesome font files
cv_contents/             ← one .tex file per section — edit these directly
  education.tex
  research_interest.tex
  Academic_positions.tex
  honors.tex
  writing.tex                 (Publications)
  presentation.tex            (Presentations)
  Funding.tex
  Service.tex
  Professional_memberships.tex
  Teaching_experience.tex
  Mentorship.tex
  Additional_training.tex
README.md                ← this file
```

## How to use it

1. Install [R](https://cran.r-project.org/) and [RStudio](https://posit.co/download/rstudio-desktop/) if you don't have them.
2. In R, install the required packages once:
   ```r
   install.packages("rmarkdown")
   tinytex::install_tinytex()   # if you don't already have a LaTeX distribution
   ```
3. Open `cv.Rmd` in RStudio and click **Knit** (or run `rmarkdown::render("cv.Rmd")`).
4. A `cv.pdf` will be created in the same folder.

Keep `cv.Rmd`, `preamble.tex`, the `cv_contents/` folder, and `fonts/` together — the styling, sections, and fonts won't load correctly if they're separated.

## Making a different CV/resume variant

This works exactly like your old `resume_basic.tex` / `resume_Pfizer.tex` files: copy `cv.Rmd` (or `resume_short_example.Rmd`) to a new filename, then comment out or remove whichever `\input{cv_contents/...}` lines you don't want for that version. For example, a short teaching-focused resume might only need:

```
\input{cv_contents/education.tex}
\input{cv_contents/Academic_positions.tex}
\input{cv_contents/Teaching_experience.tex}
```

`resume_short_example.Rmd` in this folder shows exactly that — knit it to see a 2-page trimmed-down version. Every section file is self-contained, so any combination works.

## Editing a section file

Each file in `cv_contents/` is plain LaTeX using a small set of custom commands (defined in `preamble.tex`) instead of the original `awesome-cv` macros:

- `\cvsection{Title}` — starts the section, with the bold heading + trailing rule.
- `\cvsubsection{Title}` — a centered italic subheading within a section (e.g. "Active" under Grants, "Oral" under Presentations).
- `\cvrow{<date>}{<content>}` — a two-column entry with spacing after it (used for Professional Experience, Grants, Mentorship, Additional Training). Use `\newline` inside `<content>` to add another line (e.g. between title, organization, and description), and `\textbf{...}` for bold.
- `\cvrowtight{<date>}{<content>}` — same layout, no spacing after (used for dense single-line lists: Honors, Service, Memberships, Teaching).
- `\cveduc{<degree>}{<institution>}{<location>}{<date>}` — the Education-style layout (institution/degree on the left, location/date right-aligned).

Example — adding a new job to `Academic_positions.tex`:
```
\cvrow{2026 - Present}{\textbf{New Job Title} \newline Some University, Some Department}
```

Since these are raw LaTeX files, remember to escape `&` as `\&` and `%` as `\%` (same as your original `.tex` files).

**Publications and Presentations** (`writing.tex` and `presentation.tex`) are written as numbered lists rather than pulled from `Nicky_bib.bib` via biblatex, so adding a new one is just adding a new `\item` line in the same citation style — no `.bib`/biber step required.

`Nicky_bib.bib` is included in this folder for reference/backup (it's where the current entries were originally sourced from), but the current setup doesn't read it — `writing.tex` and `presentation.tex` are self-contained.

The **header block** (name, title, address, contact icons) lives directly in `cv.Rmd` (and `resume_short_example.Rmd`) above the `\input` lines, since it's specific to each variant — feel free to shorten it for a resume version.

A `\faGithub` icon command is also defined in `preamble.tex` if you want to add a GitHub link to the header.
