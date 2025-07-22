import os
import uvicorn

if __name__ == "__main__":
    port = os.getenv("PORT") or 8085
    uvicorn.run("main:app", host="0.0.0.0", port=int(port), reload=True)
