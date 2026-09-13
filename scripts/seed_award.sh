#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

"${PYTHON_BIN}" manage.py shell <<'PY'
from datetime import date

from main.models import Award


award_records = [
    {
        "title": "Finalist — National Programming Contest (NPC) Junior",
        "description": (
            "One of 20 finalists selected from over 200 participants in a competitive programming contest."
        ),
        "thumbnail": "/static/img/Schematic.jpeg",
        "issuer": "SCHEMATICS, Institut Teknologi Sepuluh Nopember",
        "date_received": date(2024, 10, 1),
    },
    {
        "title": "Finalist — Indonesia National Competition in Informatics (NOI) 2024",
        "description": (
            "One of 100 finalists selected from over 20,000 contestants through a two-stage selection process."
        ),
        "thumbnail": "/static/img/OSN.jpeg",
        "issuer": "Balai Pengembangan Talenta Indonesia",
        "date_received": date(2024, 8, 1),
    },
    {
        "title": "3rd Place — Diponegoro Logic Competition",
        "description": "Placed third among over 100 teams of three students in a logic competition.",
        "thumbnail": "/static/img/ANFORCOM.jpeg",
        "issuer": "Diponegoro University",
        "date_received": date(2023, 9, 1),
    },
]

for record in award_records:
    date_received = record.pop("date_received")
    award, created = Award.objects.update_or_create(
        title=record["title"],
        defaults=record,
    )

    # date_received uses auto_now_add in the current model, so update the
    # historical award date directly after saving the record.
    Award.objects.filter(pk=award.pk).update(date_received=date_received)

    action = "Created" if created else "Updated"
    print(f"{action}: {award.title}")
PY
