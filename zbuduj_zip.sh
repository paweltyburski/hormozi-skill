#!/bin/sh
# Buduje hormozi.zip (folder hormozi/ w korzeniu archiwum) bez pamięci podręcznej i śmieci systemowych.
cd "$(dirname "$0")" || exit 1
rm -f hormozi.zip
zip -r -X -q hormozi.zip hormozi -x '*/.cache/*' '*.DS_Store' '*__pycache__*'
ls -l hormozi.zip
