"""Populate the database with a demo dataset so a fresh install is clickable.

Creates the seed users, then a handful of studies from synthetic chest X-rays in
mixed workflow states (some just uploaded, some predicted and awaiting review,
some fully reviewed/finalized).

Run: ``python -m app.demo``
"""
from __future__ import annotations

from app.core.db import SessionLocal
from app.models.study import Study
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewFindingIn
from app.services import study_service, review_service
from app.utils.images import synthetic_cxr
from app.seed import seed

DEMO_PATIENTS = [
    ("P-1001", "PA", "predict"),
    ("P-1002", "AP", "review"),
    ("P-1003", "PA", "upload"),
    ("P-1004", "PA", "review"),
    ("P-1005", "LAT", "predict"),
    ("P-1006", "AP", "upload"),
]


def run():
    seed()  # ensure model version + radiologist user
    db = SessionLocal()
    try:
        reviewer = db.query(User).filter_by(role="radiologist").first()

        existing = {s.patient_code for s in db.query(Study).all()}
        created = 0
        for i, (code, view, target) in enumerate(DEMO_PATIENTS):
            if code in existing:
                continue
            study = study_service.create_study(
                db, patient_code=code, view=view, filename=f"{code}.png",
                content=synthetic_cxr(seed=i), user_id=reviewer.id if reviewer else None,
            )
            created += 1

            if target in ("predict", "review"):
                prediction = study_service.run_prediction(db, study, user_id=reviewer.id)

                if target == "review" and reviewer:
                    # Confirm the AI's findings as-is to finalize the study.
                    review_service.create_review(
                        db, study,
                        ReviewCreate(
                            decision="confirmed",
                            prediction_id=prediction.id,
                            final_report="Laudo de demonstração — achados confirmados.",
                            final_findings=[
                                ReviewFindingIn(finding_code=f.finding_code, final_label=f.is_positive)
                                for f in prediction.findings
                            ],
                        ),
                        reviewer_id=reviewer.id,
                    )
        print(f"Demo data ready: {created} new studies created.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
