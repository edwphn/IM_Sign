from datetime import datetime, timezone


class DocumentTimestamp:
    def __init__(self):
        self.now = datetime.now(timezone.utc)

    def get_signing_date(self):
        """Возвращает дату в формате для подписи."""
        return self.now.strftime("D:%Y%m%d%H%M%S+00'00'")

    def get_db_format(self):
        """Возвращает дату в формате, совместимом с datetime2 в SQL Server."""
        return self.now.isoformat()


# Пример использования:
timestamp = DocumentTimestamp()
signing_date = timestamp.get_signing_date()  # Для подписи
db_format = timestamp.get_db_format()  # Для БД

print(signing_date)
print(db_format)
