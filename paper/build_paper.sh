#!/usr/bin/env bash
# Rebuild the paper (PDF and Word) from paper.md. Needs pandoc; the PDF step needs Node + Playwright.
set -e
cd "$(dirname "$0")"
pandoc paper.md -f markdown+raw_html -t docx --lua-filter=pagebreak.lua --resource-path=.:.. -o METABRIC_Clinical_Outcomes_Paper.docx
pandoc paper.md -f markdown+raw_html -t html5 -s --metadata pagetitle="METABRIC paper" --css paper.css -o paper.html
npx playwright@1.48.2 pdf --paper-format=A4 paper.html METABRIC_Clinical_Outcomes_Paper.pdf
