from fastapi import FastAPI

app = FastAPI()

@app.get("/") # Define this function as a endpoint
def read_root():
    return {"Ronald" : "Hello, Climate Data, this is myu favorite project"}