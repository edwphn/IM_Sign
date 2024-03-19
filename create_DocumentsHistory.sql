IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DocumentsHistory' AND type = 'U')
AND EXISTS (SELECT * FROM sys.tables WHERE name = 'Documents' AND type = 'U')
BEGIN
    CREATE TABLE DocumentsHistory (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        UUID uniqueidentifier NOT NULL,
        Status NVARCHAR(50) NOT NULL,
        Message NVARCHAR(MAX) NULL,
        RecordTime DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (UUID) REFERENCES Documents(UUID)
    );
END
