from fastapi import FastAPI
app = FastAPI()
@app.get("/health")
def health():
    return {"message": "ok", "status": 200}



def main():
    print("Hello from md!")


if __name__ == "__main__":
    main()
