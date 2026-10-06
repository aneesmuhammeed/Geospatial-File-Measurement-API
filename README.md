# Geospatial File Measurement API

A FastAPI backend service that accepts geospatial files (Shapefile in `.zip`, or `.kml`), processes the features within them, and returns measurement information.

## Minimum Requirements Satisfied
- **Backend Framework**: FastAPI.
- **File Upload**: `POST /api/files/` handles `.zip` (Shapefile) and `.kml`.
- **File Processing**: Extracts Feature ID, Geometry type, Geometry, CRS, and Properties.
- **Measurements**: Calculates Area for Polygons, Length for LineStrings.
- **CRS Handling**: Accurately projects geographic coordinates (e.g., EPSG:4326) using `geopandas`' `estimate_utm_crs()` to the appropriate UTM zone for accurate metric area and length calculations.
- **API Design**: `POST /api/files/`, `GET /api/files/{id}/`, `GET /api/files/{id}/measurements/` implemented.

## Setup Instructions

### Prerequisites
- Python 3.9+
- `pip` or `uv` package manager.

### 1. Create a Virtual Environment and Install Dependencies
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the Application
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000/`. You can view the interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

---

## API Documentation

### 1. Upload a File
**Endpoint**: `POST /api/files/`

**Description**: Uploads a `.zip` containing a Shapefile or a `.kml` file.

**Request**: Form-data with a `file` field containing the file.

**Response**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "survey.kml",
  "feature_count": 120,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

### 2. Get File Information
**Endpoint**: `GET /api/files/{id}/`

**Description**: Returns metadata about the uploaded file.

**Response**: (Same as above)

### 3. Get Measurements
**Endpoint**: `GET /api/files/{id}/measurements/`

**Description**: Returns measurements for all features in the file.

**Response**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "measurements": [
    {
      "feature_index": 0,
      "geometry_type": "Polygon",
      "area": 145000.5,
      "length": null
    },
    {
      "feature_index": 1,
      "geometry_type": "LineString",
      "area": null,
      "length": 450.2
    }
  ]
}
```

---

## Architecture

### Application Structure
The application follows a standard RESTful structure with FastAPI:
- `main.py`: Contains API route definitions and app initialization.
- `models.py`: SQLAlchemy ORM models representing the SQLite database schema (`UploadedFile` and `Feature`).
- `schemas.py`: Pydantic models for data validation and API response structures.
- `services.py`: Contains the core business logic, including file processing and geospatial operations.
- `database.py`: SQLAlchemy engine and session configuration.

### File-Processing Flow
1. **Upload**: The file is received via `POST /api/files/` and saved temporarily.
2. **Read**: `geopandas.read_file` is used to load the file (using the KML driver for `.kml` and the `zip://` URI for shapefiles).
3. **Save & Clean**: Extracted features are parsed, transformed into SQLAlchemy models, and saved to the SQLite database. The temporary file is then deleted.

### Measurement Calculation Flow & CRS Handling
1. **CRS Detection**: The CRS of the uploaded file is detected using `gdf.crs`.
2. **Reprojection**: To accurately calculate Area and Length, geographic coordinate systems (like EPSG:4326) are inherently inaccurate if not transformed.
    - We use the `geopandas.GeoDataFrame.estimate_utm_crs()` method.
    - This dynamically calculates the most appropriate Universal Transverse Mercator (UTM) zone for the geometries' centroid and returns an optimal projected CRS.
3. **Calculation**: The geometry is transformed into the UTM projection, and `.area` or `.length` properties are accessed. These are accurately returned in squared meters (for Area) and meters (for Length).

## Design Decisions

- **FastAPI**: Chosen over Django because it's asynchronous, extremely fast, and inherently validates payloads via Pydantic. It provides out-of-the-box Swagger documentation which is excellent for API evaluation.
- **SQLite**: Used for persistence instead of an in-memory dictionary. SQLite is zero-configuration but demonstrates how the app would scale to PostgreSQL with PostGIS in a real-world scenario.
- **GeoPandas & Fiona**: `geopandas` provides a powerful API for handling CRS and measurements gracefully, masking the complexity of manual shape extraction. We enabled the KML driver in Fiona explicitly as it's disabled by default.
- **Synchronous Processing**: The file processing currently blocks the upload request. In a production setting with large files, I would use a message queue like Celery or RQ to handle processing in the background, updating the file status from `PENDING` to `COMPLETED` asynchronously.

## Learning & Future Scope
- **Learning**: Implementing KML parsing required enabling the fiona KML driver explicitly, which was an interesting edge case compared to standard Shapefiles. Additionally, utilizing `estimate_utm_crs()` was a more robust way to handle arbitrary CRSs compared to hardcoding EPSG:3857 (Web Mercator).
- **Future Scope**: 
  - Add Celery/Redis for background file processing of large Shapefiles.
  - Implement a PostgreSQL + PostGIS database to run actual spatial queries instead of calculating and storing statically on upload.
  - Add API endpoints to query features based on spatial intersections (e.g. "Find all features within this bounding box").
  - Containerize the application using Docker for easier deployment.
