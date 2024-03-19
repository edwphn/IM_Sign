from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from datetime import datetime, timezone
import sys

# Path to your PFX file
pfx_path = 'load_certificate/certificate.pfx'

# PFX file password
pfx_password = '123456'

try:
    # Read the PFX file
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()

    # Load the PFX
    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
        pfx_data, pfx_password.encode(), default_backend()
    )

    # Check expiration
    current_time = datetime.now(timezone.utc)
    if certificate.not_valid_after_utc < current_time:
        print("Certificate has expired.")
    else:
        print("Certificate is valid. Expires on:", certificate.not_valid_after_utc)

    # Optionally, print certificate details
    print("Issuer:", certificate.issuer.rfc4514_string())
    print("Subject:", certificate.subject.rfc4514_string())

except Exception as e:
    print("An error occurred:", e)
    sys.exit(1)
