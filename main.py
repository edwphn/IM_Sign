# main.py

from _logger import logger, logging_config
import os
import uuid
from pydantic import BaseModel
from _cert import CERTS
from _config import DIR_TEMP
import _database
import maintenance
from sign_handler import sign_flow
from validators import valid_file, sanitize_input
from fastapi import FastAPI, BackgroundTasks, Header, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse

app = FastAPI()

# Maintenance on startup
logger.info("Initializing maintenance.")
app.add_event_handler("startup", maintenance.check_directories)
app.add_event_handler("startup", maintenance.create_tables)
app.add_event_handler("startup", maintenance.check_certificates)
app.add_event_handler("startup", maintenance.start_scheduler)
app.add_event_handler("shutdown", maintenance.shutdown_scheduler)


class SignResponse(BaseModel):
    uuid: str


@app.post("/sign", response_model=SignResponse, summary="Sign a file")
async def sign(
        request: Request,
        background_tasks: BackgroundTasks,
        sender: str = Header(..., description="The identifier of the file sender", alias='sender'),
        cert_name: str = Header(..., description="The name of the certificate to use for signing the file",
                                alias='cert-name')
) -> JSONResponse:
    """
    Sign a file using a specified certificate and return the file UUID along with HTTP headers indicating the task status.

    - **request**: FastAPI request object containing the file sent by the client.
    - **background_tasks**: Background tasks for asynchronous operations.
    - **sender**: Sender identifier, provided through a request header.
    - **cert_name**: Certificate name for signing, provided through a request header.
    """
    sender = sanitize_input(sender)
    cert_name = sanitize_input(cert_name)
    file_uuid = str(uuid.uuid4())
    logger.info(f"Sender {sender} queued a new file with UUID: {file_uuid}. Required certificate: {cert_name}")

    content = await request.body()
    file_size = len(content)

    if cert_name not in CERTS:
        msg = f"Required certificate is unknown: {cert_name}."
        logger.warning(msg)
        raise HTTPException(status_code=400, detail=msg)

    if not await valid_file(content):
        msg = f"Invalid file. Check the file integrity or size limit 20 MB. UUID: {file_uuid}"
        logger.warning(msg)
        raise HTTPException(status_code=400, detail=msg)

    try:
        await _database.execute_query(_database.insert_Documents, (file_uuid, None, file_size, sender))
        await _database.execute_query(_database.insert_DocumentsHistory,
                                      (file_uuid, 'Received', 'Received file from the client'))
        logger.info(f"Inserted new document UUID: {file_uuid} into database.")
    except Exception as e:
        msg = f"Database operation failed for UUID: {file_uuid}. Error: {e}"
        logger.error(msg)
        raise HTTPException(status_code=500, headers={"Task-Status": "Failed"}, detail=msg)

    background_tasks.add_task(sign_flow, content, cert_name, file_uuid)

    return JSONResponse(content={"uuid": file_uuid}, headers={"Task-Status": "Completed"}, status_code=200)


@app.get("/get_signed/{file_uuid}", responses={
    200: {
        "description": "Returns the signed PDF file to the client.",
        "content": {"application/pdf": {}}
    },
    202: {
        "description": "File is still being processed. Try again later."
    },
    400: {
        "description": "Invalid UUID format provided."
    },
    404: {
        "description": "File not found or no such UUID in database."
    },
    410: {
        "description": "File was processed and removed from the server."
    },
    422: {
        "description": "Error processing the file due to internal state."
    }
})
async def get_signed(file_uuid: str, background_tasks: BackgroundTasks):
    """
    Retrieve a signed PDF file by its UUID. This endpoint checks the file's status in the database,
    ensures the file exists on disk, and sends it to the client. If the file is not ready or encounters
    issues, appropriate status messages and codes are returned.
    """
    try:
        file_uuid = uuid.UUID(file_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format.", headers={"Task-Status": "Failed"})

    status = await _database.fetch_sql(_database.check_file_status, file_uuid)

    if not status:
        logger.warning(f'UUID: {file_uuid} - No such UUID in database.')
        raise HTTPException(status_code=404, detail="No such UUID in database.", headers={"Task-Status": "Failed"})

    elif status[0] == 'Saved':
        file_path = f"{DIR_TEMP}/{file_uuid}.pdf"

        if not os.path.exists(file_path):
            logger.warning(f'UUID: {file_uuid} - Can\'t locate file on disk.')
            raise HTTPException(status_code=404, detail="Oooops! File was lost.", headers={"Task-Status": "Failed"})

        response = FileResponse(path=file_path, headers={"Task-Status": "Completed"})
        background_tasks.add_task(handle_file_post_send, file_uuid, file_path)

        logger.info(f'UUID: {file_uuid} - Transmitted to the client.')

        return response

    elif status[0] == 'Failed':
        error_message = status[1] if len(status) > 1 else "File processing failed with an unknown error."
        logger.warning(f'UUID: {file_uuid} - {error_message}')
        return JSONResponse(content={"error": error_message}, headers={"Task-Status": "Failed"}, status_code=422)

    elif status[0] == 'Transmitted':
        warning = "File was processed, transmitted to the client and removed from the database."
        logger.warning(f'UUID: {file_uuid} - {warning}')
        return JSONResponse(content={"warning": warning}, headers={"Task-Status": "Failed"}, status_code=410)

    elif status[0] in ['Received', 'Signed']:
        message = f'The file is still being processed, please try again later. Current status: {status[0]}'
        logger.info(f'UUID: {file_uuid} - {message}')
        return JSONResponse(content={"status": message}, headers={"Task-Status": "In Progress"}, status_code=202)

    else:
        logger.error(f'Status for {file_uuid} is {status}')
        raise HTTPException(status_code=404, detail="Unexpected status", headers={"Task-Status": "Failed"})


async def handle_file_post_send(file_uuid: uuid.UUID, file_path: str):
    try:
        os.remove(file_path)
    except (PermissionError, FileNotFoundError) as e:
        logger.error(f"Problem with deleting file {e}.")
    else:
        logger.info(f"File {file_path} has been removed from disk after transmission.")

        await _database.execute_query(
            _database.insert_DocumentsHistory, (file_uuid, 'Transmitted', 'File was sent back to the client.')
        )
        logger.info(f"Recorded in the database that file {file_uuid} was transmitted.")


@app.get("/health")
async def health_check():
    """
    Health Check Endpoint

    This endpoint is used to verify that the API is operational and responding to requests.
    It returns a JSON object with the current status of the API.

    Responses:
    - `200 OK`: Success response with the status indicating that the API is alive.
    """
    return JSONResponse(content={"status": "Alive"}, status_code=200)


if __name__ == "__main__":
    logger.info("Starting FastAPI server")
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=logging_config)
