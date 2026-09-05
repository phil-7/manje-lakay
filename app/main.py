from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Manje Lakay API is running!"}
