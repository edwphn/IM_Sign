CREATE TABLE documents (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    UUID uniqueidentifier NOT NULL UNIQUE,
    FileName NVARCHAR(500) NULL,
    OriginalDocId NVARCHAR(500) NULL,
    FileSize INT NULL,
    RecordTime DATETIME NOT NULL,
    Sender NVARCHAR(255) NULL
);

CREATE TABLE document_status_history (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    UUID uniqueidentifier NOT NULL,
    Status NVARCHAR(50) NOT NULL,
    Message NVARCHAR(MAX) NULL,
    SignTimestamp DATETIME2 NOT NULL,
    RecordTime DATETIME NOT NULL,
    FOREIGN KEY (UUID) REFERENCES documents(UUID)
);