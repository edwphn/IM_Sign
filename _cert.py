# _cert.py

import os
import sys
from datetime import datetime, timezone
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.fernet import Fernet
from _database import execute_sql_sync, fetch_sql_sync
from _config import DIR_CERTIFICATE, ENCRYPTION_KEY
from _logger import logger


cipher_suite = Fernet(ENCRYPTION_KEY)


class Certificate:
    directory = DIR_CERTIFICATE

    def __init__(self, name, password='123456'):
        self.name = name
        self.password = password
        self.pfx_encrypted = None
        self.pfx_decrypted = None
        self.private_key = None
        self.certificate = None
        self.issuer = None
        self.expiration = None
        self.subject = None
        self.file_path = os.path.join(self.directory, f"{self.name}.pfx")

        if not self.fetch_valid_certificate():
            if not self.load_from_disk():
                logger.critical("Unable to load a valid certificate. Terminating program.")
                sys.exit(1)
            else:
                self._extract_certificate()
                self._check_validity()
                self._encrypt_certificate()
                self._insert_cert_to_db()
                self._delete_from_disk()
        else:
            self._decrypt_data()
            self._extract_certificate()
            self._check_validity()

    def fetch_valid_certificate(self):
        sql_query = """
        SELECT TOP 1 CertificateData FROM dbo.Certificates WHERE Valid = 1 AND CertName = ? ORDER BY ID DESC
        """
        results = fetch_sql_sync(sql_query, [self.name])
        if results:
            self.pfx_encrypted = results[0][0]
            return True
        logger.warning(f"No valid certificates found in the database for {self.name}.")
        return False

    def load_from_disk(self) -> bool:
        logger.info("Trying to load new certificate from the disk.")
        if os.path.exists(self.file_path):
            logger.info(f"Found certificate: {os.path.basename(self.file_path)}.")
            try:
                logger.info(f"Opening certificate {os.path.basename(self.file_path)}")
                with open(self.file_path, 'rb') as f:
                    self.pfx_decrypted = f.read()
                return True
            except (IOError, PermissionError) as e:
                logger.error(f"Error reading certificate from {self.file_path}: {e}")
                return False
        else:
            logger.warning(f"Certificate file not found: {os.path.basename(self.file_path)}.")
            return False

    def _extract_certificate(self) -> None:
        try:
            self.private_key, self.certificate, additional_certificates = pkcs12.load_key_and_certificates(
                self.pfx_decrypted, self.password.encode(), default_backend()
            )
            self.expiration = self.certificate.not_valid_after.astimezone(timezone.utc)
            self.issuer = self.certificate.issuer.rfc4514_string(),
            self.issuer = self.issuer[0]
            self.subject = self.certificate.subject.rfc4514_string()

            logger.info(f"Expiration: {self.expiration}. Issuer: {self.issuer}. Subject: {self.subject}")
        except Exception as e:
            logger.critical(f"An error occurred while extracting certificate: {e}")
            sys.exit(1)
        else:
            logger.success(f"Certificated {self.name} successfully extracted.")

    def _encrypt_certificate(self) -> None:
        try:
            with open(self.file_path, 'rb') as file:
                certificate_data = file.read()
            logger.info(f'File {self.name} was encrypted.')
            self.pfx_encrypted = cipher_suite.encrypt(certificate_data)
        except Exception as e:
            logger.error(f"An error occurred: {e}.")

    def _decrypt_data(self) -> None:
        try:
            self.pfx_decrypted = cipher_suite.decrypt(self.pfx_encrypted)
        except Exception as e:
            logger.critical(f"Decryption error: {e}")
            sys.exit(1)

    def _check_validity(self) -> None:
        if self.expiration < datetime.now(timezone.utc):
            logger.critical("Certificate has expired.")
            sys.exit(1)
        logger.warning(f'Certificate {self.name} will expire on: {self.expiration}')

    def _insert_cert_to_db(self):
        try:
            sql_insert = """
            INSERT INTO dbo.Certificates (Valid, Expiration, CertName, Issuer, Subject, CertificateData)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            execute_sql_sync(sql_insert, (1, self.expiration, self.name, self.issuer, self.subject, self.pfx_encrypted))

            logger.info(f"Encrypted file {os.path.basename(self.file_path)} was loaded to database.")
        except Exception as e:
            logger.error(f"Error occurred while inserting certificate to database: {e}")

    def _delete_from_disk(self):
        try:
            pass
            # os.remove(self.file_path)
        except (PermissionError, FileNotFoundError) as e:
            logger.error(f"Problem with deleting file {e}.")
        else:
            logger.success(f"The file {os.path.basename(self.file_path)} was removed from the disk.")



