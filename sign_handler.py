# _sign_pdf.pdf
import asyncio
import time

from endesive import pdf
from datetime import datetime, timezone
import aiofiles
from _cert import CERTS
import _database
from _logger import logger
from _config import DIR_TEMP


class SignTime:
    def __init__(self):
        self.now = datetime.now(timezone.utc)

    def db(self):
        return self.now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def sign(self):
        formatted_date = self.now.strftime("D:%Y%m%d%H%M%S+00'00'")
        return formatted_date.encode()


async def save_signed_file(file_content, file_uuid):
    file_path = f'{DIR_TEMP}/{file_uuid}.pdf'
    try:
        async with aiofiles.open(file_path, 'wb') as file:
            await file.write(file_content)
    except IOError as e:
        await _database.execute_query(_database.insert_DocumentsHistory,
                                      (file_uuid, 'Failed', 'Failed to save signed file to the filesystem'))
        logger.error(f"Failed to save file {file_uuid}. Error: {e}")
    else:
        await _database.execute_query(_database.insert_DocumentsHistory,
                                      (file_uuid, 'Saved', 'Signed file saved successfully'))
        logger.info(f"Saved: {file_uuid}.")


async def sign_pdf(data: bytes, cert_name: str, file_uuid: str):
    logger.debug(f'Initializing signing process for {file_uuid} with certificate {cert_name}.')
    timestamp = SignTime()
    dct = {
        "sigpage": 0,
        "contact": "pisarev@infomatic.cz",
        "location": "Prague",
        "reason": "Document verification.",
        "signingdate": timestamp.sign(),
        "sigflagsft": 132,
    }

    private_key = CERTS[cert_name].private_key
    certificate = CERTS[cert_name].certificate

    try:
        signature = pdf.cms.sign(data, dct, private_key, certificate, [], "sha256")
    except Exception as e:
        logger.error(f"PDF signing failed: {e}")
        raise
    else:
        await _database.execute_query(_database.insert_DocumentsHistory, (file_uuid, 'Signed', 'File was signed'))
        await _database.execute_query(_database.update_Documents, (timestamp.db(), file_uuid))
        logger.info(f"Signed {file_uuid} with {cert_name}.")

    return data + signature


async def sign_flow(file_content, cert_name, file_uuid):
    # await asyncio.sleep(30)
    signed_content = await sign_pdf(file_content, cert_name, file_uuid)
    await save_signed_file(signed_content, file_uuid)
