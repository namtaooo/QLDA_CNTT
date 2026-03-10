from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.routes.deps import get_current_user
from app import models

router = APIRouter()

class OfficeActionRequest(BaseModel):
    action_type: str # 'format_table', 'generate_slide', 'summarize_doc'
    content: str
    app: str # 'word', 'excel', 'powerpoint'

class OfficeActionResponse(BaseModel):
    macro_script: str
    explanation: str

@router.post("/generate-macro", response_model=OfficeActionResponse)
def generate_office_macro(
    *,
    db: Session = Depends(get_db),
    request: OfficeActionRequest,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    # Dummy implementation for now
    # Will connect to AI engine to generate specific VBA or OfficeJS scripts based on user requests
    if request.app == 'excel' and request.action_type == 'format':
        script = "function main(workbook: ExcelScript.Workbook) { let sheet = workbook.getActiveWorksheet(); sheet.getRange('A1:D1').getFormat().getFill().setColor('yellow'); }"
        explanation = "Script tô vàng dòng tiêu đề."
    else:
        script = "console.log('Action not perfectly mapped yet');"
        explanation = "Mô hình AI đang được cập nhật cho hành động này."

    return OfficeActionResponse(
        macro_script=script,
        explanation=explanation
    )
