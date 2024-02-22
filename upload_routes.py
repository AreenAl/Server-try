
from pathlib import Path
from shutil import copyfileobj
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse
import os
import boto3
from db import connect


router = APIRouter()

AWS_ACCESS_KEY_ID = "AKIA6ODU2VAY2OOX7IEZ"
AWS_SECRET_ACCESS_KEY = "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"

S3_BUCKET_NAME = os.getenv("server-try")
# Create an S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


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
    file_content = await file.read()
    bucket_name = 'server-try'
    key = f'{file_name}{Path(file.filename).suffix}'  # Using file name as the key
    try:
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
        s3.put_object(Bucket=bucket_name, Key=key, Body=file_content)
        add_db(s3_url)
        return {"message": "File uploaded successfully."}
    except Exception as e:
        return {"message": f"Failed to upload file to S3: {e}"}


def add_db(url):
    conn = connect()  # Establish database connection
    cursor = conn.cursor()
    query = """
        UPDATE users 
        SET image_path = %s
        WHERE id = %s
        """
    cursor.execute(query, (url, 2))  # Assuming user_id is available in your code
    conn.commit()  # Commit the transaction
    conn.close()  # Close the database connection
