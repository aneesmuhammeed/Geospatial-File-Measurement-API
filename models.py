from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    filename = Column(String, index=True)
    feature_count = Column(Integer, default=0)
    crs = Column(String, default="Unknown")
    status = Column(String, default="PENDING")
    
    features = relationship("Feature", back_populates="file", cascade="all, delete")

class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("uploaded_files.id"))
    feature_index = Column(Integer)
    geometry_type = Column(String)
    geometry = Column(JSON)  # Store as GeoJSON representation
    properties = Column(JSON)
    area = Column(Float, nullable=True)
    length = Column(Float, nullable=True)

    file = relationship("UploadedFile", back_populates="features")
