"""Employees and Faculty management router."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.database import add_student, get_student_by_id, get_students, remove_student
from app.schemas import StudentCreate, StudentResponse

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("", response_model=List[StudentResponse])
def list_employees(search: Optional[str] = Query(None)):
    """List all registered employees/faculty with attendance summaries."""
    return get_students(search=search)


@router.get("/{employee_id}")
def employee_detail(employee_id: int):
    """Get detailed attendance history for a single employee."""
    emp = get_student_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.post("", status_code=status.HTTP_201_CREATED)
def create_employee_endpoint(payload: StudentCreate):
    """Enroll/register a new employee in the database."""
    try:
        new_emp = add_student(name=payload.name, student_id=payload.id)
        return new_emp
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{employee_id}", status_code=status.HTTP_200_OK)
def delete_employee_endpoint(employee_id: int):
    """Delete an employee record and associated logs."""
    deleted = remove_student(employee_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"success": True, "message": f"Employee {employee_id} removed"}
