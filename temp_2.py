async def validate_file(request: Request, file_path: str, size_limit: int):
    async def check_file_size(request: Request, file_path: str, size_limit: int) -> bool:
        total_size = 0
        async with aiofiles.open(file_path, 'wb') as out_file:
            async for chunk in request.stream():
                total_size += len(chunk)
                if total_size > size_limit:
                    return False
                await out_file.write(chunk)
        return True

    def validate_pdf_file(file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if len(pdf_reader.pages) > 0:
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False