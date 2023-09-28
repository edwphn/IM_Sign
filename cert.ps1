$thumbprint = "F9222972D2206649761121EF7009198F4DEFCB92"
$cert = Get-ChildItem -Path cert:\CurrentUser\My | Where-Object { $_.Thumbprint -eq $thumbprint }


$password = ConvertTo-SecureString -String "123456" -Force -AsPlainText
Export-PfxCertificate -cert $cert.PSPath -FilePath C:\Users\pisarev\Desktop\sign\output.pfx -Password $password
