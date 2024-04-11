from _cert import Certificate
from _config import CERTIFICATES


certs = {name: Certificate(name) for name in CERTIFICATES.split(',')}

certs
