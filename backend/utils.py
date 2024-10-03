import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import base64


def decrypt(encrypted_message):
    with open("./private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)

    decrypted = private_key.decrypt(
        base64.b64decode(encrypted_message),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return decrypted.decode()


user = os.getenv("USER") or os.getenv("USERNAME")
DEBUG = False if user == "azureuser" else True
hosts = [
    {"name": "4090-s1", "port": 1721},
    {"name": "4090-s2", "port": 1722},
    {"name": "4090-s3", "port": 1723},
    {"name": "TNT", "port": 1745},
]
# 敏感信息
username = "NWqdXxrbB9iu2ISs/6V/YxTsu8ChJ5M6kSZPV/2JR3TlGadbYd9lC7JZ0vrh7YyzeSBnY47kvOJ3aCbt042AM/gl1aztkPVJONbFGQDeL/2sizvuQCt3fRMeUYJNLKWczRPYdooCMhFCkIqcnOR+UOYyWbpgF/1D5y46GjpEjqJbSrjuPppTGdJQThzdGNlxeNbkG6ue1kecHQd4IbpOoXVGzCprNToYjm/j5vva2LCLHJ0ESI6gXf2LV1CAf6xFgxiiDboQ9DnW3Y/GqAp/aFtQwXXpNnvK4hPcOMB+q/YNkGQZ0/iy/rOkrQ+sKBHY8HpBF72iKbtE5O10/t51+Q=="
hostname = "mArMWhfrPxKorUjCt1S2oyvHx9UitZjbv7YEEOoJ25BBwPXoAxbskKPmuzEpRuRj2SKjD/xTYW1ut6nEySu/gmdD0w4i6mwbNzIzhNhC8FeyG7/20A+RUC9uWmKd3nqKlbELa9EhY8s/3nrOGmd0/zmHBIIxj0iqUTIKXpQ6GBjOAnHhIi21aSo3bMRastB9piNtJXdkIIUE85nGE1UygVyHBik+iMWfrHoQTtnDVZFlisPLKhrbZNvlcjdf4D42h/kwAJHT+OII8JSZzpJ8F60+y7ZIIdlANnVuR64xyGpGSY5HQr2RruG2l40ecy2gs5w5SEzfKbY5sQGZa82HMQ=="
username = decrypt(username)
hostname = decrypt(hostname)
key_file = (
    "/Users/shengyuye/.ssh/id_ed25519" if DEBUG else "/home/azureuser/.ssh/id_ed25519"
)

PYTHON = "/data/ShengyuYe/miniconda3/bin/python"
GET_CPU_USAGE_SCRTPTS = """
import psutil
cpu_usage = psutil.cpu_percent(interval=1)
memory_info = psutil.virtual_memory()
cpu_memory_usage = memory_info.percent
print(cpu_usage, cpu_memory_usage)
"""
