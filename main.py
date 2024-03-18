from fastapi import FastAPI, Header, Request, HTTPException
import uuid
from datetime import datetime, timezone
from database_handler import create_tables, execute_sql, insert_Sign_PDF, insert_Sign_PDF_history
from validators import validate_file
import aiofiles

app = FastAPI()

app.add_event_handler("startup", create_tables)


@app.post("/sign")
async def sign(request: Request, sender: str = Header(...)):
    file_uuid = str(uuid.uuid4())
    print(file_uuid)

    content = await request.body()

    # Validate file
    is_valid = await validate_file(content)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid file. Check file integrity or size limit.")

    file_path = f"files/{file_uuid}.pdf"
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(content)

    now = datetime.now(timezone.utc)
    file_size = len(content)

    await execute_sql(insert_Sign_PDF, (file_uuid, now, 'unknown.pdf', None, file_size, now, sender))
    await execute_sql(insert_Sign_PDF_history, (file_uuid, 'Received', 'Received file from the client', now))

    return {"uuid": file_uuid}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
