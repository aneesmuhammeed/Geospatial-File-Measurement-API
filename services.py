import os
import shutil
import geopandas as gpd
import fiona
from fastapi import UploadFile
from sqlalchemy.orm import Session
import models
import tempfile
import json
from shapely.geometry import mapping

# Enable KML support in fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

def process_and_save_geodata(db: Session, db_file: models.UploadedFile, file_path: str, filename: str):
    try:
        if filename.endswith(".kml"):
            gdf = gpd.read_file(file_path, driver="KML")
        elif filename.endswith(".zip"):
            gdf = gpd.read_file(f"zip://{file_path}")
        else:
            raise ValueError("Unsupported file format. Please upload .zip (Shapefile) or .kml.")

        # Extract CRS
        db_file.crs = str(gdf.crs) if gdf.crs else "Unknown"
        db_file.feature_count = len(gdf)

        # Reproject to a suitable projected CRS for accurate area and length calculations
        # estimate_utm_crs() is useful if the data is in geographic coordinates.
        gdf_projected = None
        if gdf.crs:
            try:
                gdf_projected = gdf.to_crs(gdf.estimate_utm_crs())
            except Exception as e:
                print(f"Could not reproject to UTM: {e}")
                gdf_projected = gdf # Fallback to original
        else:
            gdf_projected = gdf # Can't accurately project without CRS
            
        features_to_insert = []
        for index, row in gdf.iterrows():
            geom = row.geometry
            if geom is None:
                continue

            geom_type = geom.geom_type
            
            # Use the projected geometry for measurements
            projected_geom = gdf_projected.iloc[index].geometry
            
            area = None
            length = None
            
            if geom_type in ["Polygon", "MultiPolygon"]:
                area = projected_geom.area if projected_geom else None
            elif geom_type in ["LineString", "MultiLineString"]:
                length = projected_geom.length if projected_geom else None
                
            # Properties
            properties = {}
            for col in gdf.columns:
                if col != "geometry":
                    val = row[col]
                    # Handle basic serialization for JSON
                    if isinstance(val, (int, float, str, bool)):
                        properties[col] = val
                    elif val is None:
                        properties[col] = None
                    else:
                        properties[col] = str(val)

            feature_record = models.Feature(
                file_id=db_file.id,
                feature_index=index,
                geometry_type=geom_type,
                geometry=mapping(geom),
                properties=properties,
                area=area,
                length=length
            )
            features_to_insert.append(feature_record)
            
        db.add_all(features_to_insert)
        db_file.status = "COMPLETED"
        db.commit()

    except Exception as e:
        print(f"Error processing file: {e}")
        db_file.status = "FAILED"
        db.commit()
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

async def handle_file_upload(db: Session, file: UploadFile):
    db_file = models.UploadedFile(filename=file.filename)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Save to temp file
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{db_file.id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Process file synchronously for simplicity in this example. 
    # In a real production app, this should be sent to a Celery/Redis worker.
    process_and_save_geodata(db, db_file, file_path, file.filename)
    
    db.refresh(db_file)
    return db_file
