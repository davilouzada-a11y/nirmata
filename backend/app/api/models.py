from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.model_version import ModelVersion
from app.models.user import User

router = APIRouter()


@router.get("/versions")
def list_model_versions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    return [
        {"id": m.id, "name": m.name, "version": m.version,
         "training_dataset": m.training_dataset, "threshold_config": m.threshold_config,
         "created_at": m.created_at}
        for m in versions
    ]
