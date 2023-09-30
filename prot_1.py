import os
import traceback
import sys
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import base64
import pyodbc
from loguru import logger


app = FastAPI()

class File(BaseModel):
    content: str
    metadata: dict


class SignedFile(BaseModel):
    signed_content: str


@app.post("/sign/", response_model=SignedFile)
async def sign_file(file_data: File):
    try:
        # Декодирование файла из base64
        decoded_file = base64.b64decode(file_data.content)

        # Ваш код для создания подписи
        # ...

        signed_data = "your_signed_data_here"  # Это просто заглушка
        return {"signed_content": signed_data}
    except Exception as e:
        logger.exception("Error during file signing:")
        raise HTTPException(status_code=500, detail="Error during file signing")


@app.post("/validate/")
async def validate_file(file_data: File):
    try:
        # Декодирование файла из base64
        decoded_file = base64.b64decode(file_data.content)

        # Ваш код для валидации файла
        # ...

        validation_result = "your_validation_result_here"  # Это просто заглушка
        return {"status": "success", "validation_result": validation_result}
    except Exception as e:
        logger.exception("Error during file validation:")
        raise HTTPException(status_code=500, detail="Error during file validation")


if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.exception("An unexpected error occurred:")
        exc_info = sys.exc_info()
        tb_str = "".join(traceback.format_exception(*exc_info))
        logger.error("Traceback: \n" + tb_str)
        sys.exit(1)
