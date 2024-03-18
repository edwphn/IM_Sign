import re
import PyPDF2
from io import BytesIO
import asyncio

async def validate_file(file_content: bytes) -> bool:
    async def check_file_size() -> bool:
        max_size = 1011183
        return len(file_content) <= max_size

    async def check_pdf_integrity_async() -> bool:
        # This wrapper function allows us to run the synchronous check_pdf_integrity function in a thread
        def check_pdf_integrity() -> bool:
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
                return len(pdf_reader.pages) > 0
            except Exception as e:
                print(f"Unexpected error: {e}")
                return False

        # Run the synchronous function in a separate thread to avoid blocking the async loop
        return await asyncio.to_thread(check_pdf_integrity)

    if not await check_file_size():
        return False

    if not await check_pdf_integrity_async():
        return False

    return True


def sanitize_input(input_str: str) -> str:
    sanitized_str = re.sub(r'<script.*?>.*?</script>', '', input_str, flags=re.DOTALL)
    sanitized_str = re.sub(r'<.*?>', '', sanitized_str)

    special_chars = ["'", '"', ";", "--"]
    for char in special_chars:
        sanitized_str = sanitized_str.replace(char, "")

    return sanitized_str
