"""
System configuration models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from database import Base


class SystemConfig(Base):
    """System configuration settings."""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    value_type = Column(String(20), nullable=False, default="string")  # string, boolean, integer, json
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(50))  # Admin username who made the change

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"

    @property
    def parsed_value(self):
        """Parse the value based on its type."""
        if self.value_type == "boolean":
            return str(self.value).lower() in ("true", "1", "yes", "on")
        elif self.value_type == "integer":
            try:
                return int(str(self.value))
            except (ValueError, TypeError):
                return 0
        elif self.value_type == "json":
            import json
            try:
                return json.loads(str(self.value))
            except (ValueError, TypeError):
                return {}
        else:
            return str(self.value)

    @classmethod
    def set_value(cls, db, key: str, value, value_type: str = "string", description: str = None, updated_by: str = "admin"):
        """Set or update a configuration value."""
        config = db.query(cls).filter(cls.key == key).first()
        
        # Convert value to string for storage
        if value_type == "boolean":
            str_value = "true" if value else "false"
        elif value_type == "json":
            import json
            str_value = json.dumps(value)
        else:
            str_value = str(value)
        
        if config:
            config.value = str_value
            config.value_type = value_type
            config.updated_at = datetime.utcnow()
            config.updated_by = updated_by
            if description:
                config.description = description
        else:
            config = cls(
                key=key,
                value=str_value,
                value_type=value_type,
                description=description or f"System setting: {key}",
                updated_by=updated_by
            )
            db.add(config)
        
        db.commit()
        return config

    @classmethod
    def get_value(cls, db, key: str, default=None):
        """Get a configuration value with optional default."""
        config = db.query(cls).filter(cls.key == key).first()
        if config:
            return config.parsed_value
        return default