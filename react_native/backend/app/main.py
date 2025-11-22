from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.validators import check_image_corruption


app = FastAPI(
    title="AgriGuard Image Validation API",
    description="Advanced image corruption and security validation API for AgriGuard platform",
    version="1.0.0"
)

# CORS configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AgriGuard Image Validation API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "image-validation"}

@app.post("/validate-image")
async def validate_image(file: UploadFile = File(...)):
    file_bytes = await file.read()
    results = check_image_corruption(file_bytes)
    return results
