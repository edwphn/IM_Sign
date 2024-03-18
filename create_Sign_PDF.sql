IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sign_PDF' AND type = 'U')
BEGIN
    CREATE TABLE Sign_PDF (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        UUID uniqueidentifier NOT NULL UNIQUE,
        SignTimestamp DATETIME2 NULL,
        FileName NVARCHAR(500) NULL,
        OriginalDocId NVARCHAR(500) NULL,
        FileSize INT NULL,
        RecordTime DATETIME NOT NULL,
        Sender NVARCHAR(255) NULL
    );
END
