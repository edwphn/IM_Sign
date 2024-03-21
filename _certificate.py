# _certificate.py

import os
import sys
from datetime import datetime, timezone
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.fernet import Fernet
from _database import execute_sql_sync
from config_loader import config_vars
from log_sett import logger


folder_path = config_vars['DIRECTORIES']['CERTIFICATE']
encryption_key = config_vars['ENCRYPTION']['KEY']

cipher_suite = Fernet(encryption_key)


def get_certificate_metadata(cert_data):
    try:
        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
            cert_data, '123456'.encode(), default_backend()
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


def get_latest_valid_certificate():
    sql_query = "SELECT TOP 1 CertificateData FROM dbo.Certificates WHERE Valid = 1 ORDER BY RecordTime DESC"
    encrypted_data_row = execute_sql_sync(sql_query)
    if not encrypted_data_row:
        raise ValueError("No valid certificates found in the database.")
    return encrypted_data_row[0][0]


def check_certificate_validity():
    try:
        encrypted_certificate_data = get_latest_valid_certificate()
        if not encrypted_certificate_data:
            logger.error("No valid certificate in database.")
            return False
        else:
            decrypted_certificate_data = cipher_suite.decrypt(encrypted_certificate_data)

            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                decrypted_certificate_data, b'123456', default_backend()
            )

            if certificate:
                if certificate.not_valid_after < datetime.now(timezone.utc):
                    logger.error("Certificate has expired.")
                    return False
                else:
                    logger.success("Certificate is valid.")
                    logger.warning(f"Expires on: {certificate.not_valid_after}.")
                    return True
            else:
                logger.error("Certificate in database looks corrupted after decryption.")
                return False

    except Exception as e:
        logger.error(f"An error occurred while checking the certificate: {e}.")
        return False
