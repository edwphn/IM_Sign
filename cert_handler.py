import os
import pyodbc
from cryptography.fernet import Fernet

# Конфигурация
folder_path = 'path_to_your_special_folder'  # Путь к папке с сертификатами
db_conn_str = 'DRIVER={SQL Server};SERVER=your_server_name;DATABASE=your_database_name;UID=your_username;PWD=your_password;'  # Строка подключения к базе данных
encryption_key = b'your_fernet_key'  # Ключ для шифрования (генерируется один раз и сохраняется в безопасности)

# Создание объекта для шифрования
cipher_suite = Fernet(encryption_key)

def encrypt_and_upload_certificate(file_path):
    # Чтение и шифрование файла сертификата
    with open(file_path, 'rb') as file:
        certificate_data = file.read()
    encrypted_data = cipher_suite.encrypt(certificate_data)

    # Подключение к базе данных и загрузка зашифрованных данных
    conn = pyodbc.connect(db_conn_str)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO YourTable (YourColumn) VALUES (?)", encrypted_data)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Сертификат {os.path.basename(file_path)} зашифрован и загружен в базу данных.")


# Проверка папки на наличие сертификатов
for filename in os.listdir(folder_path):
    if filename.endswith('.pfx'):
        file_path = os.path.join(folder_path, filename)
        encrypt_and_upload_certificate(file_path)
        # Удаление файла сертификата после загрузки в базу данных
        os.remove(file_path)
        print(f"Файл {os.path.basename(file_path)} удалён.")
