#!/usr/bin/env bash
# Compile the LaTeX CV and publish the PDF the website links to.
#
#   bin/cv/build_pdf.sh                  one-page CV  -> assets/pdf/Zancanaro_CV.pdf
#   bin/cv/build_pdf.sh --long           long CV      -> assets/pdf/Zancanaro_CV_extended.pdf
#   bin/cv/build_pdf.sh --profile industry_ml --suffix industry_ml
#   bin/cv/build_pdf.sh --no-copy        build only, leave assets/pdf/ alone
#
# Run it locally; it is not wired into CI. Nothing here runs automatically.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CV_TEX="$REPO/cv_tex"
OUT_DIR="$REPO/assets/pdf"
BASE="Zancanaro_CV"

LONG=0; PROFILE=""; SUFFIX=""; COPY=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --long)     LONG=1 ;;
    --profile)  PROFILE="${2:?--profile needs a name}"; shift ;;
    --suffix)   SUFFIX="${2:?--suffix needs a value}"; shift ;;
    --no-copy)  COPY=0 ;;
    -h|--help)  sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

if ! command -v pdflatex >/dev/null 2>&1; then
  cat >&2 <<'EOF'
error: pdflatex not found on PATH.

  Debian/Ubuntu: sudo apt-get install texlive-latex-recommended \
                   texlive-fonts-extra texlive-latex-extra
  macOS:         brew install --cask mactex-no-gui

  The CV needs the `lato` and `fontawesome5` packages, which live in
  texlive-fonts-extra. Overleaf has both already.
EOF
  exit 1
fi

if [[ -n "$PROFILE" ]]; then
  echo "==> regenerating cv_tex/generated for profile '$PROFILE'"
  python3 "$REPO/bin/cv/build_tex.py" --profile "$PROFILE"
fi

# pdflatex stamps a creation date and a file ID into every PDF. Pinning
# both keeps rebuilds byte-identical, so an unchanged CV is not a 160 KB
# binary diff on every run.
export SOURCE_DATE_EPOCH=0
export FORCE_SOURCE_DATE=1

TARGET=$([[ $LONG -eq 1 ]] && echo long || echo one)
echo "==> make $TARGET"
make -C "$CV_TEX" "$TARGET"

SRC=$([[ $LONG -eq 1 ]] && echo "$CV_TEX/cv_long.pdf" || echo "$CV_TEX/main.pdf")
[[ -f "$SRC" ]] || { echo "error: $SRC was not produced" >&2; exit 1; }

if [[ $COPY -eq 0 ]]; then
  echo "built $SRC (not copied)"
  exit 0
fi

NAME="$BASE"
[[ $LONG -eq 1 ]] && NAME="${NAME}_extended"
[[ -n "$SUFFIX" ]] && NAME="${NAME}_${SUFFIX}"
DEST="$OUT_DIR/${NAME}.pdf"
mkdir -p "$OUT_DIR"
cp "$SRC" "$DEST"
echo "==> published ${DEST#"$REPO"/}"

# The download button is driven by two hand-owned files. They are front
# matter with other content in them, so this script reports a mismatch
# rather than rewriting them.
WANT="/assets/pdf/${NAME}.pdf"
if [[ $LONG -eq 0 && -z "$SUFFIX" ]]; then
  bad=0
  for f in _pages/cv.md _data/socials.yml; do
    if ! grep -q "cv_pdf:.*${WANT}" "$REPO/$f"; then
      echo "warning: $f does not point cv_pdf at ${WANT}" >&2
      bad=1
    fi
  done
  [[ $bad -eq 1 ]] && echo "  (fix those two lines by hand, then re-run)" >&2
fi
exit 0
