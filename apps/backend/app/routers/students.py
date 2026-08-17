"""Students management router."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.database import add_student, get_student_by_id, get_students, remove_student
from app.schemas import StudentCreate, StudentResponse

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("", response_model=List[StudentResponse])
def list_students(search: Optional[str] = Query(None)):
    """List all registered students with attendance summaries."""
    return get_students(search=search)


@router.get("/{student_id}")
def student_detail(student_id: int):
    """Get detailed attendance history for a single student."""
    student = get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("", status_code=status.HTTP_201_CREATED)
def create_student_endpoint(payload: StudentCreate):
    """Enroll a new student in the database."""
    try:
        new_student = add_student(name=payload.name, student_id=payload.id)
        return new_student
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{student_id}", status_code=status.HTTP_200_OK)
def delete_student_endpoint(student_id: int):
    """Delete a student record and associated logs."""
    deleted = remove_student(student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"success": True, "message": f"Student {student_id} removed"}
