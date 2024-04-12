using System.Net;
using System.IO;
using Agility.Sdk.Model;
using TotalAgility.Sdk;
using Agility.Server.Scripting.ScriptAssembly;
using Agility.Sdk.Model;
using TotalAgility.Sdk;

namespace MyNamespace
{
    public class Class1
    {
        [StartMethodAttribute()]
        public void Method1(ScriptParameters sp)
        {
            try
            {
                string Session = sp.InputVariables["SPP_SYSTEM_SESSION_ID"];
                string url = sp.InputVariables["OCR_ENDPOINT"];
                string DocumentId = sp.InputVariables["DOCID"];
                string key = sp.InputVariables["ENDPOINT_KEY"];

                TotalAgility.Sdk.CaptureDocumentService CDS = new TotalAgility.Sdk.CaptureDocumentService();
                Agility.Sdk.Model.Capture.DocumentFileOptions FO = new Agility.Sdk.Model.Capture.DocumentFileOptions();
                FO.FileType="TIFF";
                System.IO.Stream STR=CDS.GetDocumentFile2(Session,null,DocumentId,FO);

                WebRequest request = WebRequest.Create(url);
                request.Method = "POST";
                request.ContentType = "application/octet-stream";
                request.Headers.Add("Ocp-Apim-Subscription-Key", key);

                byte[] fileData = new byte[STR.Length];
                STR.Read(fileData, 0, fileData.Length);
                request.ContentLength = fileData.Length;

                using (Stream requestStream = request.GetRequestStream())
                {
                    requestStream.Write(fileData, 0, fileData.Length);
                }

                using (WebResponse response = request.GetResponse())
                {
                    string operationLocation = response.Headers["Operation-Location"];
                    sp.OutputVariables["OPERATION_LOCATION"] = operationLocation;
                }
            }
            catch (WebException ex)
            {
                sp.OutputVariables["ERROR"] = ex.Message;
            }
        }
    }
}