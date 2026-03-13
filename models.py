"""Database models for SOC Agent"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum


class SeverityLevel(str, enum.Enum):
    """Severity levels for incidents and alerts"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatus(str, enum.Enum):
    """Status of security incidents"""
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class Incident(Base):
    """Security incident model"""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.NEW)
    assigned_to = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    # Relationship with alerts
    alerts = relationship("Alert", back_populates="incident", cascade="all, delete-orphan")
    comments = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value if self.severity else None,
            "status": self.status.value if self.status else None,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "alert_count": len(self.alerts) if self.alerts else 0
        }


class Alert(Base):
    """Security alert model"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    alert_type = Column(String(100))
    source_ip = Column(String(45))  # IPv6 compatible
    destination_ip = Column(String(45))
    username = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSON)  # Store original alert data as JSON

    # Relationship with incident
    incident = relationship("Incident", back_populates="alerts")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "alert_type": self.alert_type,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "username": self.username,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "raw_data": self.raw_data
        }


class IncidentComment(Base):
    """Comments on security incidents"""
    __tablename__ = "incident_comments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    author = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with incident
    incident = relationship("Incident", back_populates="comments")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "author": self.author,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DetectionRule(Base):
    """Detection rules for threat hunting"""
    __tablename__ = "detection_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM)
    enabled = Column(Integer, default=1)  # SQLite doesn't have Boolean, use 0/1
    rule_definition = Column(JSON)  # Store rule as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value if self.severity else None,
            "enabled": bool(self.enabled),
            "rule_definition": self.rule_definition,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None
        }
