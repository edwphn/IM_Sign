import base64
from fastapi import FastAPI
from pydantic import BaseModel
from endesive import pdf
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timezone
from cryptography.hazmat.primitives.serialization import pkcs12

app = FastAPI()


def get_signing_date():
    now = datetime.now(timezone.utc)
    formatted_date = now.strftime("D:%Y%m%d%H%M%S+00'00'")
    return formatted_date.encode()


class Base64Util:
    @staticmethod
    def encode(data: bytes) -> str:
        return base64.b64encode(data).decode('utf-8')

    @staticmethod
    def decode(data_str: str) -> bytes:
        return base64.b64decode(data_str)


class PDFFile(BaseModel):
    name: str
    data: str


@app.post("/sign/")
async def sign_data(pdf_file: PDFFile):
    input_binary: bytes = Base64Util.decode(pdf_file.data)
    signed_binary: bytes = sign_pdf(input_binary)
    output_base64: str = Base64Util.encode(signed_binary)
    return {"name": pdf_file.name, "data": output_base64}


def sign_pdf(input_binary: bytes) -> bytes:
    with open("load_certificate/certificate.pfx", 'rb') as f:
        pfx_data = f.read()

    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
        pfx_data, "123456".encode(), default_backend())

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
        signature = pdf.cms.sign(input_binary, dct, private_key, certificate, [], "sha256")
        return input_binary + signature
    except Exception as e:
        print(f"Exception: {e}")
        return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
