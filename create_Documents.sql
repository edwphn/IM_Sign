IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Documents' AND type = 'U')
BEGIN
    CREATE TABLE Documents (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        UUID uniqueidentifier NOT NULL UNIQUE,
        SignTimestamp DATETIME2 NULL,
        FileName NVARCHAR(500) NULL,
        OriginalDocId NVARCHAR(500) NULL,
        FileSize INT NULL,
        RecordTime DATETIME NOT NULL DEFAULT GETDATE(),
        Sender NVARCHAR(255) NULL
    );
END
