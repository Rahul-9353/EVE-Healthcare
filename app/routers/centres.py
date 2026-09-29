from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.deps import get_db, get_current_user

router = APIRouter(tags = ["centres"])

@router.post("/centres/", response_model = schemas.CentreOut, status_code = status.HTTP_201_CREATED)
def create_centre(
    payload: schemas.CentreCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    centre = models.DiagnosticCentre(name = payload.name, location = payload.location)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre

@router.get("/centres/", response_model = List[schemas.CentreOut])
def list_centres(db: Session = Depends(get_db)):
    return db.query(models.DiagnosticCentre).options(joinedload(models.DiagnosticCentre.tests)).all()

@router.get("/centres/{centre_id}", response_model = schemas.CentreOut)
def get_centre(centre_id: int, db: Session = Depends(get_db)):
    centre = (
        db.query(models.DiagnosticCentre)
        .options(joinedload(models.DiagnosticCentre.tests))
        .filter(models.DiagnosticCentre.id == centre_id)
        .first()
    )
    if not centre:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Diagnostic centre not found")
    return centre

@router.post(
    "/centres/{centre_id}/tests",
    response_model = schemas.TestOut,
    status_code = status.HTTP_201_CREATED,
)
def add_test_to_centre(
    centre_id: int,
    payload: schemas.TestCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    centre = db.query(models.DiagnosticCentre).filter(models.DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Diagnostic centre not found")

    test = models.DiagnosticTest(centre_id = centre_id, name = payload.name, price = payload.price)
    db.add(test)
    db.commit()
    db.refresh(test)
    return test

@router.get("/tests/", response_model = List[schemas.TestOut])
def list_tests(centre_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.DiagnosticTest)
    if centre_id is not None:
        query = query.filter(models.DiagnosticTest.centre_id == centre_id)
    return query.all()