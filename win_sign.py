import os
import subprocess
from endesive import pdf
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timezone
from cryptography.hazmat.primitives.serialization import pkcs12


def get_signing_date():
    now = datetime.now(timezone.utc)
    formatted_date = now.strftime("D:%Y%m%d%H%M%S+00'00'")
    return formatted_date.encode()

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

# Экспорт сертификата и ключей из хранилища
password = "123456"
output_file = "C:\\Users\\pisarev\\Desktop\\sign\\output.pfx"

# Запускаем PowerShell скрипт
cmd = 'powershell.exe -ExecutionPolicy Bypass -File C:\\Users\\pisarev\\Desktop\\sign\\cert.ps1'
subprocess.run(cmd)
with open(output_file, 'rb') as f:
    pfx_data = f.read()
os.remove(output_file)
private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
    pfx_data, password.encode(), default_backend())

input_path = 'C:\\Users\\pisarev\\Desktop\\sign\\file2.pdf'
output_path = 'C:\\Users\\pisarev\\Desktop\\sign\\file2_signed.pdf'

sign_pdf(input_path, output_path, certificate, private_key)
