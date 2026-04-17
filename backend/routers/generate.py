from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.llama_service import get_generator

router = APIRouter()


class GenerateRequest(BaseModel):
    text: str = Field(..., min_length=1)


class GenerateResponse(BaseModel):
    latex: str
    tokens_used: int
    inference_time_ms: int


class EditRequest(BaseModel):
    current_latex: str = Field(..., min_length=1)
    edit_command: str = Field(..., min_length=1)


@router.post("/generate-latex", response_model=GenerateResponse)
def generate_latex(req: GenerateRequest) -> GenerateResponse:
    latex, tokens, elapsed = get_generator().generate(req.text)
    return GenerateResponse(latex=latex, tokens_used=tokens, inference_time_ms=elapsed)


@router.post("/edit-equation", response_model=GenerateResponse)
def edit_equation(req: EditRequest) -> GenerateResponse:
    latex, tokens, elapsed = get_generator().edit(req.current_latex, req.edit_command)
    return GenerateResponse(latex=latex, tokens_used=tokens, inference_time_ms=elapsed)
