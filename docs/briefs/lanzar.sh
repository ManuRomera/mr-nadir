#!/bin/bash
# Uso: lanzar.sh <modelo> <brief.md> <log>   (desde la raíz del módulo)
cd "$(dirname "$0")/../.."
MODEL="${1:-opencode/deepseek-v4.1-flash-free}"
BRIEF="$2"; LOG="$3"
opencode run -m "$MODEL" --title "$(basename "$BRIEF")" "$(cat docs/briefs/_comun.md; echo; echo '# TAREA'; cat "$BRIEF")" > "$LOG" 2>&1
