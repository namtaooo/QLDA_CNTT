"""
Office Router — AI-powered Office integration endpoints.
"""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.routes.deps import get_current_active_user
from app import models
from app.services import office_service

router = APIRouter()


# ──── Request / Response models ────

class OfficeActionRequest(BaseModel):
    action_type: str  # 'format_table', 'generate_slide', 'summarize_doc'
    content: str
    app: str  # 'word', 'excel', 'powerpoint'

class OfficeActionResponse(BaseModel):
    macro_script: str
    explanation: str

class ExcelFormulaRequest(BaseModel):
    description: str
    cell_context: str = ""

class ExcelFormulaResponse(BaseModel):
    formula: str
    explanation: str

class WordReportRequest(BaseModel):
    topic: str
    data_context: str = ""

class WordReportResponse(BaseModel):
    report_content: str
    topic: str

class DocumentAnalysisRequest(BaseModel):
    content: str
    action: str  # 'summarize', 'translate', 'extract_key_points', etc.

class DocumentAnalysisResponse(BaseModel):
    action: str
    result: str


# ──── Legacy macro endpoint ────

@router.post("/generate-macro", response_model=OfficeActionResponse)
async def generate_office_macro(
    *,
    db: Session = Depends(get_db),
    request: OfficeActionRequest,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    result = await office_service.analyze_document_content(
        request.content, f"{request.action_type} for {request.app}"
    )
    return OfficeActionResponse(
        macro_script=result.get("result", ""),
        explanation=f"AI-generated {request.action_type} for {request.app}",
    )


# ──── Excel formula generation ────

@router.post("/excel/formula", response_model=ExcelFormulaResponse)
async def generate_excel_formula(
    *,
    request: ExcelFormulaRequest,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    result = await office_service.generate_excel_formula(
        request.description, request.cell_context
    )
    return ExcelFormulaResponse(**result)


# ──── Word report generation ────

@router.post("/word/report", response_model=WordReportResponse)
async def generate_word_report(
    *,
    request: WordReportRequest,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    result = await office_service.generate_word_report(
        request.topic, request.data_context
    )
    return WordReportResponse(**result)


# ──── Document content analysis ────

@router.post("/analyze-content", response_model=DocumentAnalysisResponse)
async def analyze_document(
    *,
    request: DocumentAnalysisRequest,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    result = await office_service.analyze_document_content(
        request.content, request.action
    )
    return DocumentAnalysisResponse(**result)
