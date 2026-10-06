from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, get_db
import models, schemas, services
from fastapi.middleware.cors import CORSMiddleware

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Geospatial File Measurement API", description="API to process geospatial files and return measurements.")

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/files/", response_model=schemas.FileResponse, status_code=201)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.endswith(".zip") or file.filename.endswith(".kml")):
        raise HTTPException(status_code=400, detail="Only .zip (Shapefile) and .kml files are supported.")
    
    db_file = await services.handle_file_upload(db, file)
    return db_file

@app.get("/api/files/{file_id}/", response_model=schemas.FileResponse)
def get_file_info(file_id: str, db: Session = Depends(get_db)):
    db_file = db.query(models.UploadedFile).filter(models.UploadedFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    return db_file

@app.get("/api/files/{file_id}/measurements/", response_model=schemas.MeasurementListResponse)
def get_file_measurements(file_id: str, db: Session = Depends(get_db)):
    db_file = db.query(models.UploadedFile).filter(models.UploadedFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    features = db.query(models.Feature).filter(models.Feature.file_id == file_id).all()
    
    return {
        "id": file_id,
        "measurements": features
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
