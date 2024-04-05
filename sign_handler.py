# _sign_pdf.pdf

from endesive import pdf
from datetime import datetime, timezone
import aiofiles
import _cert
import _database
from log_sett import logger
from _config import config_vars


class SignTime:
    def __init__(self):
        self.now = datetime.now(timezone.utc)

    def db(self):
        return self.now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def sign(self):
        formatted_date = self.now.strftime("D:%Y%m%d%H%M%S+00'00'")
        return formatted_date.encode()


async def save_signed_file(file_content, file_uuid):
    now = datetime.now(timezone.utc)
    file_path = f'{config_vars["DIRECTORIES"]["TEMP"]}/{file_uuid}.pdf'
    try:
        async with aiofiles.open(file_path, 'wb') as file:
            await file.write(file_content)
    except IOError as e:
        await _database.execute_query(_database.insert_DocumentsHistory,
                                      (file_uuid, 'Failed', 'Failed to save signed file to the filesystem', now))
        logger.error(f"Failed to save signed file {file_uuid}. Error: {e}")
    else:
        await _database.execute_query(_database.insert_DocumentsHistory,
                                      (file_uuid, 'Saved', 'Signed file saved successfully', now))
        logger.info(f"Signed file saved successfully: {file_uuid}")


async def sign_pdf(file_uuid, data, pfx_data):
    try:
        private_key, certificate = _cert.extract_certificate(pfx_data)
    except Exception as e:
        logger.error(f"Failed to extract certificate: {e}")
        raise

    current_datetime = SignTime()
    dct = {
        "sigpage": 0,
        "contact": "pisarev@infomatic.cz",
        "location": "Prague",
        "reason": "Document verification.",
        "signingdate": current_datetime.sign(),
        "sigflagsft": 132,
    }

    try:
        signature = pdf.cms.sign(data, dct, private_key, certificate, [], "sha256")
    except Exception as e:
        logger.error(f"PDF signing failed: {e}")
        raise
    else:
        now = datetime.now(timezone.utc)
        await _database.execute_query(_database.insert_DocumentsHistory, (file_uuid, 'Signed', 'File was signed', now))

    return data + signature


async def sign_flow(file_content, file_uuid):
    logger.info(f'Starting signing process for: {file_uuid}')
    signed_content = await sign_pdf(file_uuid, file_content, _cert.decrypted_certificate_data)

    logger.info(f'Saving on filesystem: {file_uuid}')
    await save_signed_file(signed_content, file_uuid)
