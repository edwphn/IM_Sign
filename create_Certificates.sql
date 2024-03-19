IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Certificates' AND type = 'U')
BEGIN
    CREATE TABLE Certificates (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        Valid BIT NOT NULL,
        Expiration DATETIME NOT NULL,
        Issuer NVARCHAR(MAX) NULL,
        Subject NVARCHAR(MAX) NULL,
        RecordTime DATETIME NOT NULL DEFAULT GETDATE(),
        CertificateData VARBINARY(MAX)
    );
END
