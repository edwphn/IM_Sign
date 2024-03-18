IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sign_PDF_history' AND type = 'U')
AND EXISTS (SELECT * FROM sys.tables WHERE name = 'Sign_PDF' AND type = 'U')
BEGIN
    CREATE TABLE Sign_PDF_history (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        UUID uniqueidentifier NOT NULL,
        Status NVARCHAR(50) NOT NULL,
        Message NVARCHAR(MAX) NULL,
        RecordTime DATETIME NOT NULL,
        FOREIGN KEY (UUID) REFERENCES Sign_PDF(UUID)
    );
END
