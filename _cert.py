# _cert.py

import os
from datetime import datetime, timezone
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.fernet import Fernet
from _database import execute_sql_sync, fetch_sql_sync
from _config import DIR_CERTIFICATE, ENCRYPTION_KEY
from log_sett import logger


decrypted_certificate_data = None

cipher_suite = Fernet(ENCRYPTION_KEY)


def encrypt_certificate(file_path):
    with open(file_path, 'rb') as file:
        certificate_data = file.read()
    return cipher_suite.encrypt(certificate_data)


def extract_certificate(cert_data):
    try:
        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
            cert_data, '123456'.encode(), default_backend()
        )

        return private_key, certificate

    except Exception as e:
        logger.critical(f"An error occurred: {e}")


def load_certificates_from_disk() -> None:
    for filename in os.listdir(DIR_CERTIFICATE):
        if filename.endswith('.pfx'):
            logger.info(f"Found certificate: {filename}")

            file_path = os.path.join(DIR_CERTIFICATE, filename)
            with open(file_path, 'rb') as f:
                pfx_data = f.read()

            try:
                extracted_private_key, extracted_certificate = extract_certificate(pfx_data)

                expiration = extracted_certificate.not_valid_after_utc,
                issuer = extracted_certificate.issuer.rfc4514_string(),
                subject = extracted_certificate.subject.rfc4514_string()
            except Exception as e:
                logger.critical(f"An error occurred while processing certificate {filename}: {e}")
                continue

            encrypted_data = encrypt_certificate(file_path)

            logger.info(f"Expiration: {expiration}. Issuer: {issuer}. Subject: {subject}")

            sql_insert = """
            INSERT INTO dbo.Certificates (Valid, Expiration, Issuer, Subject, CertificateData)
            VALUES (?, ?, ?, ?, ?)
            """
            execute_sql_sync(sql_insert, (1, expiration, issuer, subject, encrypted_data))

            # os.remove(file_path)
            logger.info(f"File {os.path.basename(file_path)} was loaded to database and removed from the disk.")


def get_latest_valid_certificate():
    sql_query = "SELECT TOP 1 CertificateData FROM dbo.Certificates WHERE Valid = 1 ORDER BY RecordTime DESC"
    encrypted_data_row = fetch_sql_sync(sql_query)
    if not encrypted_data_row:
        raise ValueError("No valid certificates found in the database.")
    return encrypted_data_row[0][0]


def check_certificate_validity() -> bool:
    global decrypted_certificate_data
    try:
        encrypted_certificate_data = get_latest_valid_certificate()
        if not encrypted_certificate_data:
            logger.warning("No valid certificate in database found.")
            return False
        else:
            decrypted_certificate_data = cipher_suite.decrypt(encrypted_certificate_data)
            certificate = extract_certificate(decrypted_certificate_data)[1]

            if certificate:
                not_valid_after_utc = certificate.not_valid_after.astimezone(timezone.utc)

                if not_valid_after_utc < datetime.now(timezone.utc):
                    logger.error("Certificate has expired.")
                    return False
                else:
                    logger.warning(f"Certificate expires on: {not_valid_after_utc}.")
                    return True
            else:
                logger.error("Certificate in database looks corrupted after decryption.")
                return False

    except Exception as e:
        logger.error(f"An error occurred while checking the certificate: {e}")
        return False


# TODO - Сделать класс по управлению сертификатами
# class Certificate:
#     def __init__(self, name, db_connection, disk_path):
#         self.name = name
#         self.private_key = None
#         self.certificate = None
#         self.issuer = None
#         self.expiration_date = None
#         self.subject = None
#         self.db_connection = db_connection
#         self.disk_path = disk_path
#
#         if not self.load_from_db():
#             if not self.load_from_disk():
#                 raise ValueError("Unable to load a valid certificate.")
#
#     def load_from_db(self):
#         """Загружает сертификат из БД. Возвращает True, если загрузка успешна."""
#         # Здесь реализация загрузки сертификата из БД
#         # Пример: self.certificate = db_connection.get_certificate(self.name)
#         # После загрузки проверяем валидность
#         return self.check_validity()
#
#     def load_from_disk(self):
#         """Загружает сертификат с диска. Возвращает True, если загрузка успешна."""
#         # Здесь реализация загрузки сертификата с диска
#         # Пример: self.certificate = load_certificate_from_path(self.disk_path)
#         # После загрузки проверяем валидность и загружаем в БД
#         if self.check_validity():
#             self.upload_to_db()
#             return True
#         return False
#
#     def check_validity(self):
#         """Проверяет сертификат на валидность. Возвращает True, если сертификат валиден."""
#         # Здесь реализация проверки валидности
#         # Можно проверить expiration_date и другие параметры
#         return True
#
#     def upload_to_db(self):
#         """Загружает валидный сертификат в БД."""
#         # Здесь реализация загрузки сертификата в БД
#         pass

