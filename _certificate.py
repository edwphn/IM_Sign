# _certificate.py

import os
import sys
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.fernet import Fernet
from _database import execute_sql_sync
from config_loader import config_vars


folder_path = config_vars['DIRECTORIES']['CERTIFICATE']
encryption_key = config_vars['ENCRYPTION']['KEY']

cipher_suite = Fernet(encryption_key)

def get_certificate_metadata(pfx_path):
    pfx_password = '123456'

    try:
        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
            pfx_data, pfx_password.encode(), default_backend()
        )

        return certificate.not_valid_after_utc, certificate.issuer.rfc4514_string(), certificate.subject.rfc4514_string()

    except Exception as e:
        print("An error occurred:", e)


def encrypt_certificate(file_path):
    with open(file_path, 'rb') as file:
        certificate_data = file.read()
    return cipher_suite.encrypt(certificate_data)


for filename in os.listdir(folder_path):
    if filename.endswith('.pfx'):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'rb') as f:
            pfx_data = f.read()
        expiration, issuer, subject = get_certificate_metadata(pfx_data)
        encrypted_data = encrypt_certificate(file_path)

        print(expiration, issuer, subject, encrypted_data)

        sql_insert = """
        INSERT INTO dbo.Certificates (Valid, Expiration, Issuer, Subject, CertificateData)
        VALUES (?, ?, ?, ?, ?)
        """
        execute_sql_sync(sql_insert, (1, expiration, issuer, subject, encrypted_data))

        # os.remove(file_path)
        print(f"File {os.path.basename(file_path)} was deleted.")
