# main.py

from fastapi import FastAPI, Header, Request, HTTPException
import uuid
from datetime import datetime, timezone
from database_handler import create_tables, execute_sql, insert_Documents, insert_DocumentsHistory
from maintenance import maintenance
from validators import validate_file, sanitize_input
import aiofiles
from log_sett import logger


# Maintenance on startup
maintenance()

logger.info('Program started')
app = FastAPI()

app.add_event_handler("startup", create_tables)

@app.post("/sign")
async def sign(request: Request, sender: str = Header(...)):
    sender = sanitize_input(sender)
    file_uuid = str(uuid.uuid4())
    logger.info(f"Generated UUID for file: {file_uuid} from sender: {sender}")

    content = await request.body()

    # Validate file
    is_valid = await validate_file(content)
    if not is_valid:
        logger.warning(f"File validation failed for UUID: {file_uuid}")
        raise HTTPException(status_code=400, detail="Invalid file. Check the file integrity or size limit.")

    file_path = f"data/{file_uuid}.pdf"
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(content)
        logger.info(f"File saved successfully at {file_path}")
    except IOError as e:
        logger.error(f"Failed to save file for UUID: {file_uuid}. Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file.")

    now = datetime.now(timezone.utc)
    file_size = len(content)

    try:
        await execute_sql(insert_Documents, (file_uuid, now, 'unknown.pdf', None, file_size, now, sender))
        await execute_sql(insert_DocumentsHistory, (file_uuid, 'Received', 'Received file from client', now))
        logger.info(f"Database operations successful for UUID: {file_uuid}")
    except Exception as e:
        logger.error(f"Database operation failed for UUID: {file_uuid}. Error: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed.")

    return {"uuid": file_uuid}

if __name__ == "__main__":
    logger.info("Starting FastAPI server on 127.0.0.1:8000")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
