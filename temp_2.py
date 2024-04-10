import os
import sys
from datetime import datetime, timezone
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.fernet import Fernet
from _database import execute_sql_sync, fetch_sql_sync
from _config import DIR_CERTIFICATE, ENCRYPTION_KEY
from _logger import logger

decrypted_certificate_data = None

cipher_suite = Fernet(ENCRYPTION_KEY)


class CertificateBase:
    def __init__(self, name, password='123456', file_type='pfx'):
        self.name = name
        self.type = file_type
        self.file_name = f"{self.name}.{self.type}"
        self.password = password
        self.pfx_encrypted = None
        self.pfx_decrypted = None


class FileManager:
    def __init__(self, directory, certificate_base: CertificateBase):
        self.data_directory = directory
        self.certificate_base = certificate_base
        self.name = self.certificate_base.name
        self.file_path = os.path.join(self.data_directory, self.certificate_base.file_name)

    def load_from_disk(self) -> bool:
        try:
            logger.info(f"Opening the file: {self.name}")
            with open(self.file_path, 'rb') as f:
                self.certificate_base.pfx_decrypted = f.read()
            return True
        except (IOError, PermissionError, FileNotFoundError) as e:
            logger.error(f"Error while reading file: {self.name}: {e}")
            return False

    def delete_from_disk(self):
        try:
            logger.info(f"Removing file {self.file_name} from the disk.")
            os.remove(self.file_path)
            logger.error(f"Couldn't find the file: {self.file_path}.")
        except (PermissionError, FileNotFoundError) as e:
            logger.error(f"Problem with deleting file {e}.")
        else:
            logger.success(f"The file {os.path.basename(self.file_path)} was removed from the disk.")


class CertificateProcessor:
    @staticmethod
    def extract_certificate_details(pfx_data, password):
        try:
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data, password.encode(), default_backend()
            )
            details = {
                'expiration': certificate.not_valid_after,
                'issuer': certificate.issuer.rfc4514_string(),
                'subject': certificate.subject.rfc4514_string(),
            }
            logger.info(f"Extracted details: {details}")
            return details
        except Exception as e:
            logger.critical(f"Error extracting certificate details: {e}")
            return None


# Assuming the existence of `fetch_sql_sync` and `execute_sql_sync` functions.

class CertificateStorageManager:
    @staticmethod
    def fetch_valid_certificate(name):
        sql_query = f"SELECT TOP 1 CertificateData FROM dbo.Certificates WHERE Valid = 1 AND Name = '{name}' ORDER BY ID DESC"
        results = fetch_sql_sync(sql_query)
        if results:
            return results[0][0]
        return None

    @staticmethod
    def insert_cert_to_db(name, details, pfx_encrypted):
        try:
            sql_insert = """INSERT INTO dbo.Certificates (Valid, Expiration, CertName, Issuer, Subject, CertificateData)
                            VALUES (?, ?, ?, ?, ?, ?)"""
            execute_sql_sync(sql_insert, (1, details['expiration'], name, details['issuer'], details['subject'], pfx_encrypted))
            logger.info(f"Certificate {name} inserted into database.")
        except Exception as e:
            logger.error(f"Error inserting certificate into database: {e}")


class CertificateManager:
    def __init__(self, name, directory):
        self.certificate_base = CertificateBase(name, directory)
        self.file_manager = FileManager()
        self.processor = CertificateProcessor()
        self.storage_manager = CertificateStorageManager()

    def manage_certificate(self):
        # This method would orchestrate loading, processing, storing the certificate.
        # Implement the logic as per the original __init__ method, utilizing the refactored components.
        pass

