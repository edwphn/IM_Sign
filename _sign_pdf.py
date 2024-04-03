# _sign_pdf.pdf

from endesive import pdf
from datetime import datetime, timezone
import aiofiles
from log_sett import logger
from config_loader import config_vars


def get_signing_date():
    now = datetime.now(timezone.utc)
    formatted_date = now.strftime("D:%Y%m%d%H%M%S+00'00'")
    return formatted_date.encode()


async def save_signed_file(file_content, file_name):
    try:
        async with aiofiles.open(file_name, 'wb') as file:
            await file.write(file_content)
        logger.success(f"Signed file saved successfully: {file_name}")
    except IOError as e:
        logger.error(f"Failed to save signed file {file_name}. Error: {e}")


async def sign_file(content):
    return content + b" Signed"


def sign_pdf(input_file, output_file, certificate, private_key):
    with open(input_file, 'rb') as f:
        data = f.read()

    dct = {
        "sigpage": 0,
        "contact": "pisarev@infomatic.cz",
        "location": "Prague",
        "reason": "Document verification.",
        "signingdate": get_signing_date(),
        "sigflagsft": 132,
        # "tsa_url": "https://freetsa.org/tsr",  # URL TSA
    }

    try:
        signature = pdf.cms.sign(data, dct, private_key, certificate, [], "sha256")
        with open(output_file, 'wb') as f:
            f.write(data + signature)

    except Exception as e:
        print(f"Exception: {e}")

async def sign_flow(file_content, file_uuid):
    signed_content = await sign_file(file_content)
    file_path = f"{config_vars["DIRECTORIES"]["TEMP"]}/{file_uuid}.pdf"
    await save_signed_file(signed_content, file_path)
