#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

"${PYTHON_BIN}" manage.py shell <<'PY'
from datetime import date

from main.models import Experience


experience_records = [
    {
        "title": "Software Engineer Staff at Compfest 18",
        "description": (
            "Compfest is one of biggest tech festivals in Indonesia by Faculty of Computer Science, "
            "Universitas Indonesia, giving Competition, Academy, Workshops, and more"
        ),
        "keyfeatures": [
            "Developed and maintained the platform's frontend and backend components",
            "Worked with SOLID design principles and clean architecture to maintain a large codebase",
        ],
        "start_at": date(2026, 3, 1),
        "ended_at": None,
    },
    {
        "title": "Fullstack Developer at DDP0",
        "description": (
            "DDP0 is a project by Arung 25 designed to introduce programming fundamentals to freshman "
            "students, helping them build a strong foundation before taking the DDP-1 course."
        ),
        "keyfeatures": [
            "Developed and maintained the platform's frontend and backend components",
            "Implemented auto grading system for programming exercises using Job distribution with Redis "
            "and goroutine workers to handle 400+ concurrent requests",
        ],
        "start_at": date(2026, 6, 1),
        "ended_at": date(2026, 8, 31),
    },
]

for record in experience_records:
    start_at = record.pop("start_at")
    ended_at = record.pop("ended_at")
    experience, created = Experience.objects.update_or_create(
        title=record["title"],
        defaults=record,
    )

    # start_at uses auto_now_add in the current model, so update historical
    # dates directly after saving the record.
    Experience.objects.filter(pk=experience.pk).update(
        start_at=start_at,
        ended_at=ended_at,
    )

    action = "Created" if created else "Updated"
    print(f"{action}: {experience.title}")
PY
