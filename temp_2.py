from _cert import Certificate
from _config import CERTIFICATES


for el in CERTIFICATES.split(','):
    cert = Certificate(el)
    print(cert.certificate)

