from fastapi import FastAPI
from database_handler import create_table, insert_data

app = FastAPI()

app.add_event_handler("startup", create_table)

@app.post("/sign")
async def sign():
    await insert_data()
    return {"message": "Data inserted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
