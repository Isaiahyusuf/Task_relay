from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, BigInteger
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class UserRole(PyEnum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    SUBCONTRACTOR = "subcontractor"

class JobStatus(PyEnum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class JobType(PyEnum):
    QUOTE = "quote"
    PRESET_PRICE = "preset_price"

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="team")
    jobs = relationship("Job", back_populates="team")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    access_code_id = Column(Integer, ForeignKey("access_codes.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team", back_populates="users")
    access_code = relationship("AccessCode", back_populates="users")
    created_jobs = relationship("Job", back_populates="supervisor", foreign_keys="Job.supervisor_id")
    assigned_jobs = relationship("Job", back_populates="subcontractor", foreign_keys="Job.subcontractor_id")

class AccessCode(Base):
    __tablename__ = "access_codes"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    max_uses = Column(Integer, default=1)
    current_uses = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team")
    users = relationship("User", back_populates="access_code")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    job_type = Column(Enum(JobType), nullable=False)
    preset_price = Column(String(50), nullable=True)
    quoted_price = Column(String(50), nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subcontractor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    photos = Column(Text, nullable=True)
    decline_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    dispatched_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    
    team = relationship("Team", back_populates="jobs")
    supervisor = relationship("User", back_populates="created_jobs", foreign_keys=[supervisor_id])
    subcontractor = relationship("User", back_populates="assigned_jobs", foreign_keys=[subcontractor_id])
