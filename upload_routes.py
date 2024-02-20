
from pathlib import Path
from shutil import copyfileobj
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse


router = APIRouter()
@router.get("/", response_class=HTMLResponse)
async def upload_form():
    return """
    <form action="/upload" enctype="multipart/form-data" method="post">
        <input name="file" type="file" multiple>
        <input name="file_name" type="text">
        <input type="submit">
    </form>
    """

@router.post("/")
async def upload_file(file: UploadFile = File(...), file_name: str = Form(...)):
    if not file:
        return {"message": "No upload file sent"}
    suf = Path(file.filename).suffix
    if not file_name:
        file_name = file.filename
    file_path = f"assets/{file_name+suf}"
    with open(file_path, "wb") as buffer:
        copyfileobj(file.file, buffer)
    return {"filename": file_name+suf}