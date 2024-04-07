# _cert.py

import os
import sys
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


class Certificate:
    directory = DIR_CERTIFICATE

    def __init__(self, name):
        self.name = name
        self.password = '123456'
        self.cipher_suite = Fernet(ENCRYPTION_KEY)
        self.pfx_encrypted = None
        self.pfx_decrypted = None
        self.private_key = None
        self.certificate = None
        self.issuer = None
        self.expiration_date = None
        self.subject = None
        self.file_path = os.path.join(self.directory, f"{self.name}.pfx")

        if not self.get_latest_valid_certificate():
            logger.warning("No valid certificates in the database. Trying to load new certificate from the disk.")
            if not self.load_from_disk():
                logger.critical("Unable to load a valid certificate.")
                sys.exit(1)
            else:
                self.extract_certificate()
                self.check_validity()
                self.move_certificate_to_db()
        else:
            self._decrypt_data()
            self.extract_certificate()
            self.check_validity()

    def get_latest_valid_certificate(self):
        sql_query = f"""
        SELECT TOP 1 CertificateData FROM dbo.Certificates WHERE Valid = 1 AND Name = {self.name} ORDER BY ID DESC
        """
        results = fetch_sql_sync(sql_query, [self.name])
        if results:
            self.pfx_encrypted = results[0][0]
            return True
        return False

    def load_from_disk(self) -> bool:
        if os.path.exists(self.file_path):
            logger.info(f"Found certificate: {self.file_path}.")
            try:
                with open(self.file_path, 'rb') as f:
                    self.pfx_decrypted = f.read()
                logger.info(f"Reading certificate {self.name}")
                return True
            except (IOError, PermissionError) as e:
                logger.error(f"Error reading certificate from {self.file_path}: {e}")
                return False
        else:
            logger.warning(f"Certificate file not found: {self.file_path}.")
            return False

    def extract_certificate(self) -> None:
        try:
            self.private_key, self.certificate, additional_certificates = pkcs12.load_key_and_certificates(
                self.pfx_decrypted, self.password.encode(), default_backend()
            )
            self.expiration_date = self.certificate.not_valid_after_utc,
            self.issuer = self.certificate.issuer.rfc4514_string(),
            self.subject = self.certificate.subject.rfc4514_string()

            logger.info(f"Expiration: {self.expiration_date}. Issuer: {self.issuer}. Subject: {self.subject}")

        except Exception as e:
            logger.critical(f"An error occurred: {e}")
            sys.exit(1)

    def _encrypt_certificate(self) -> bytes:
        with open(self.file_path, 'rb') as file:
            certificate_data = file.read()
        return self.cipher_suite.encrypt(certificate_data)

    def _decrypt_data(self) -> None:
        try:
            self.decrypted_data = self.cipher_suite.decrypt(self.pfx_encrypted)
        except Exception as e:
            print(f"Decryption error: {e}")
            sys.exit(1)

    def check_validity(self):
        if self.expiration_date < datetime.now(timezone.utc):
            logger.critical("Certificate has expired.")
            sys.exit(1)
        logger.warning(f'Certificate {self.name} will expire on: {self.expiration_date}')

    def move_certificate_to_db(self):
        sql_insert = """
        INSERT INTO dbo.Certificates (Valid, Expiration, Issuer, Subject, CertificateData)
        VALUES (?, ?, ?, ?, ?)
        """
        pfx_encrypted = self._encrypt_certificate()
        execute_sql_sync(sql_insert, (1, self.expiration_date, self.issuer, self.subject, pfx_encrypted))

        os.remove(self.file_path)
        logger.info(f"File {os.path.basename(self.file_path)} was loaded to database and removed from the disk.")


cert_CSAT = Certificate('CSAT')
