# main.py

import os
from _logger import logger
from _config import DIR_TEMP
import maintenance
from fastapi import FastAPI, BackgroundTasks, Header, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse
import uuid
from datetime import datetime, timezone
import _database
from validators import validate_file, sanitize_input
from sign_handler import sign_flow


app = FastAPI()

# Maintenance on startup
logger.info("Initializing maintenance.")
app.add_event_handler("startup", maintenance.check_directories)
app.add_event_handler("startup", maintenance.create_tables)
app.add_event_handler("startup", maintenance.check_certificates)


@app.post("/sign")
async def sign(
        request: Request,
        background_tasks: BackgroundTasks,
        sender: str = Header(...),
        purpose: str = Header(...)
):
    sender = sanitize_input(sender)
    purpose = sanitize_input(purpose)
    file_uuid = str(uuid.uuid4())
    logger.info(f"Generated UUID for the file: {file_uuid}. Sender: {sender}. Purpose: {purpose}")

    content = await request.body()
    now = datetime.now(timezone.utc)
    file_size = len(content)

    # Validate the file
    is_valid = await validate_file(content)
    if not is_valid:
        logger.warning(f"File validation failed for UUID: {file_uuid}")
        raise HTTPException(status_code=400, detail="Invalid file. Check the file integrity or size limit.")

    try:
        await _database.execute_query(_database.insert_Documents, (file_uuid, now, None, None, file_size, now, sender))
        await _database.execute_query(_database.insert_DocumentsHistory,
                                      (file_uuid, 'Received', 'Received file from the client', now))
        logger.success(f"Insert new document UUID: {file_uuid} into database.")
    except Exception as e:
        msg = f"Database operation failed for UUID: {file_uuid}. Error: {e}"
        logger.error(msg)
        raise HTTPException(status_code=500, headers={"Task-Status": "Failed"}, detail=msg)

    # Send the file to the signing flow
    background_tasks.add_task(sign_flow, content, file_uuid)

    return {"uuid": file_uuid}


@app.get("/get_signed/{file_uuid}")
async def get_signed(file_uuid: str):
    status = await _database.fetch_sql(_database.check_file_status, file_uuid)
    if not status:
        logger.warning(f'UUID: {file_uuid} - No such UUID in database.')
        raise HTTPException(status_code=404, detail="No such UUID in database.")

    elif status[0] == 'Saved':
        file_path = f"{DIR_TEMP}/{file_uuid}.pdf"
        if not os.path.exists(file_path):
            logger.warning(f'UUID: {file_uuid} - Can\'t locate file on disk.')
            raise HTTPException(status_code=404, detail="Oooops! File was lost.", headers={"Task-Status": "Failed"})
        logger.warning(f'UUID: {file_uuid} - Transmitted to the client.')
        return FileResponse(path=file_path, headers={"Task-Status": "Completed"})

    elif status[0] == 'Failed':
        error_message = status[1] if len(status) > 1 else "File processing failed with an unknown error."
        logger.warning(f'UUID: {file_uuid} - {error_message}')
        return JSONResponse(content={"error": error_message}, headers={"Task-Status": "Failed"}, status_code=422)

    elif status[0] == 'Transmitted':
        warning = "File was processed, transmitted to the client and removed from the database."
        logger.warning(f'UUID: {file_uuid} - {warning}')
        return JSONResponse(content={"warning": warning}, headers={"Task-Status": "Transmitted"}, status_code=410)

    elif status[0] == 'In Progress':
        message = 'The file is still being processed, please try again later.'
        logger.warning(f'UUID: {file_uuid} - {message}')
        return JSONResponse(
            content={"status": message},
            headers={"Task-Status": "In Progress"},
            status_code=202
        )

    else:
        logger.debug(f'Status for {file_uuid} is {status}')
        raise HTTPException(status_code=404, detail="Unexpected status")


if __name__ == "__main__":
    logger.info("Starting FastAPI server")
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
