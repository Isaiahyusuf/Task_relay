from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, BigInteger, Float
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class UserRole(PyEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    SUBCONTRACTOR = "subcontractor"

class AvailabilityStatus(PyEnum):
    AVAILABLE = "available"
    BUSY = "busy"
    AWAY = "away"

class JobStatus(PyEnum):
    CREATED = "CREATED"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"

class JobType(PyEnum):
    QUOTE = "quote"
    PRESET_PRICE = "preset_price"

class TeamType(PyEnum):
    NORTHWEST = "northwest"
    SOUTHEAST = "southeast"

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    team_type = Column(Enum(TeamType, values_callable=lambda x: [e.value for e in x]), nullable=True)
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
    region_id = Column(Integer, ForeignKey("regions.id", use_alter=True), nullable=True)  # Geographic region
    custom_role_id = Column(Integer, ForeignKey("custom_roles.id", use_alter=True), nullable=True)  # Custom role with permissions
    access_code_id = Column(Integer, ForeignKey("access_codes.id"), nullable=True)
    super_admin_code = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    availability_status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.AVAILABLE)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team", back_populates="users")
    access_code = relationship("AccessCode", back_populates="users")
    created_jobs = relationship("Job", back_populates="supervisor", foreign_keys="Job.supervisor_id")
    assigned_jobs = relationship("Job", back_populates="subcontractor", foreign_keys="Job.subcontractor_id")
    quotes = relationship("Quote", back_populates="subcontractor")

class AccessCode(Base):
    __tablename__ = "access_codes"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    region_id = Column(Integer, ForeignKey("regions.id", use_alter=True), nullable=True)  # Region for this code
    custom_role_id = Column(Integer, ForeignKey("custom_roles.id", use_alter=True), nullable=True)  # Custom role for this code
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
    status = Column(Enum(JobStatus), default=JobStatus.CREATED)
    
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    region_id = Column(Integer, ForeignKey("regions.id", use_alter=True), nullable=True)  # Target region for job
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subcontractor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    accepted_quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)
    
    photos = Column(Text, nullable=True)
    supervisor_photos = Column(Text, nullable=True)  # Photos attached by supervisor when creating job
    decline_reason = Column(Text, nullable=True)
    company_name = Column(String(200), nullable=True)
    
    deadline = Column(DateTime, nullable=True)  # Job deadline
    deadline_reminder_sent = Column(Boolean, default=False)  # If deadline reminder was sent
    
    rating = Column(Integer, nullable=True)
    rating_comment = Column(Text, nullable=True)
    
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    
    team = relationship("Team", back_populates="jobs")
    supervisor = relationship("User", back_populates="created_jobs", foreign_keys=[supervisor_id])
    subcontractor = relationship("User", back_populates="assigned_jobs", foreign_keys=[subcontractor_id])
    quotes = relationship("Quote", back_populates="job", foreign_keys="Quote.job_id")
    accepted_quote = relationship("Quote", foreign_keys=[accepted_quote_id], post_update=True)

class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    subcontractor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    is_accepted = Column(Boolean, default=False)
    is_declined = Column(Boolean, default=False)
    decline_reason = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="quotes", foreign_keys=[job_id])
    subcontractor = relationship("User", back_populates="quotes")

class WeeklyAvailability(Base):
    __tablename__ = "weekly_availability"
    
    id = Column(Integer, primary_key=True)
    subcontractor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_start = Column(DateTime, nullable=False)  # Monday of the week being asked about
    monday_available = Column(Boolean, default=False)
    tuesday_available = Column(Boolean, default=False)
    wednesday_available = Column(Boolean, default=False)
    thursday_available = Column(Boolean, default=False)
    friday_available = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    subcontractor = relationship("User")

class UnavailabilityNotice(Base):
    __tablename__ = "unavailability_notices"
    
    id = Column(Integer, primary_key=True)
    subcontractor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    reason = Column(Text, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    notified_supervisor_ids = Column(Text, nullable=True)  # Comma-separated supervisor IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    subcontractor = relationship("User")
    job = relationship("Job")

class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    target_role = Column(String(50), nullable=True)  # null = all, or specific role
    target_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    recipient_ids = Column(Text, nullable=True)  # Comma-separated for selected users
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    sender = relationship("User")
    target_team = relationship("Team")

class MessageResponse(Base):
    __tablename__ = "message_responses"
    
    id = Column(Integer, primary_key=True)
    broadcast_id = Column(Integer, ForeignKey("broadcast_messages.id"), nullable=False)
    responder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    response_type = Column(String(20), nullable=False)  # acknowledged, reply
    reply_text = Column(Text, nullable=True)
    responded_at = Column(DateTime, default=datetime.utcnow)
    
    broadcast = relationship("BroadcastMessage")
    responder = relationship("User")

# ============= CUSTOM ROLES & REGIONS SYSTEM =============

# Available permissions that can be assigned to custom roles
AVAILABLE_PERMISSIONS = [
    ("create_jobs", "Create Jobs"),
    ("view_own_jobs", "View Own Jobs"),
    ("view_all_jobs", "View All Jobs"),
    ("cancel_jobs", "Cancel Jobs"),
    ("complete_jobs", "Mark Jobs Complete"),
    ("send_messages", "Send Messages"),
    ("view_availability", "View Subcontractor Availability"),
    ("create_subcontractor_codes", "Create Subcontractor Codes"),
    ("create_supervisor_codes", "Create Supervisor Codes"),
    ("create_admin_codes", "Create Admin Codes"),
    ("manage_users", "Manage Users"),
    ("view_users", "View Users"),
    ("archive_jobs", "Archive Jobs"),
    ("view_archived", "View Archived Jobs"),
    ("accept_jobs", "Accept Jobs"),
    ("decline_jobs", "Decline Jobs"),
    ("submit_quotes", "Submit Quotes"),
    ("start_jobs", "Start Jobs"),
    ("submit_jobs", "Submit Completed Jobs"),
    ("set_availability", "Set Availability Status"),
    ("report_unavailability", "Report Unavailability"),
]

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    created_by = relationship("User", foreign_keys=[created_by_id])

class CustomRole(Base):
    __tablename__ = "custom_roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    base_role = Column(Enum(UserRole), nullable=False)  # Which base role this extends
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    created_by = relationship("User", foreign_keys=[created_by_id])
    permissions = relationship("RolePermission", back_populates="custom_role", cascade="all, delete-orphan")

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True)
    custom_role_id = Column(Integer, ForeignKey("custom_roles.id"), nullable=False)
    permission_key = Column(String(50), nullable=False)  # Key from AVAILABLE_PERMISSIONS
    enabled = Column(Boolean, default=True)
    
    custom_role = relationship("CustomRole", back_populates="permissions")
