# main.py
import os

from log_sett import logger
from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse
import uuid
from datetime import datetime, timezone
import _database
from maintenance import maintenance
from validators import validate_file, sanitize_input
import aiofiles
from config_loader import config_vars


app = FastAPI()
app.add_event_handler("startup", _database.create_tables)


@app.post("/sign")
async def sign(request: Request, sender: str = Header(...), purpose: str = Header(...)):
    sender = sanitize_input(sender)
    purpose = sanitize_input(purpose)
    file_uuid = str(uuid.uuid4())
    logger.info(f"Generated UUID for the file: {file_uuid}. Sender: {sender}. Purpose: {purpose}")

    content = await request.body()

    # Validate the file
    is_valid = await validate_file(content)
    if not is_valid:
        logger.warning(f"File validation failed for UUID: {file_uuid}")
        raise HTTPException(status_code=400, detail="Invalid file. Check the file integrity or size limit.")

    file_name = file_uuid + '.pdf'
    file_path = f"{config_vars["DIRECTORIES"]["TEMP"]}/{file_name}"
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(content)
        logger.success(f"File saved successfully at {file_path}")
    except IOError as e:
        logger.error(f"Failed to save file for UUID: {file_uuid}. Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file.")

    now = datetime.now(timezone.utc)
    file_size = len(content)

    try:
        await _database.execute_sql(_database.insert_Documents, (file_uuid, now, file_name, None, file_size, now, sender))
        await _database.execute_sql(_database.insert_DocumentsHistory, (file_uuid, 'Received', 'Received file from the client', now))
        logger.success(f"Database operations successful.")
    except Exception as e:
        logger.error(f"Database operation failed for UUID: {file_uuid}. Error: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed.")

    return {"uuid": file_uuid}


@app.get("/get_signed/{file_uuid}")
async def get_signed(file_uuid: str):
    status = await _database.fetch_sql(_database.check_file_status, file_uuid)
    logger.debug(f'signed: {status}')

    if not status:
        raise HTTPException(status_code=404, detail="No such UUID in database.")
    elif status[0] == 'Signed':
        file_path = f"{config_vars['DIRECTORIES']['TEMP']}/{file_uuid}.pdf"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File does not exist.")
        headers = {"Task-Status": "Completed"}
        return FileResponse(path=file_path, headers=headers)
    elif status[0] == 'Failed':
        error_message = status[1] if len(status) > 1 else "File processing failed with an unknown error."
        headers = {"Task-Status": "Failed"}
        return JSONResponse(content={"error": error_message}, headers=headers, status_code=422)
    elif status[0] == 'Transmitted':
        warning = "File was processed, transmitted to the client and removed from the database."
        headers = {"Task-Status": "Transmitted"}
        return JSONResponse(content={"warning": warning}, headers=headers, status_code=410)
    elif status[0] == 'In Progress':
        headers = {"Task-Status": "In Progress"}
        return JSONResponse(
            content={"status": "The file is still being processed, please try again later."},
            headers=headers,
            status_code=202
        )
    else:
        raise HTTPException(status_code=404, detail="Unexpected status")


if __name__ == "__main__":
    # Maintenance on startup
    maintenance()

    logger.info("Starting FastAPI server on 127.0.0.1:8000")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
