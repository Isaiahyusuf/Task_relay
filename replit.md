# TaskRelay Bot

## Overview
TaskRelay Bot is a Telegram-based workflow automation system for managing job assignments between Supervisors, Subcontractors, and Admins.

## Project Structure
```
src/bot/
├── main.py              # Entry point
├── config.py            # Environment configuration
├── database/
│   ├── __init__.py
│   ├── models.py        # SQLAlchemy models (User, Job, AccessCode, Team)
│   └── session.py       # Database session management
├── handlers/
│   ├── __init__.py
│   ├── auth.py          # Authentication and /start, /help
│   ├── supervisor.py    # Job creation and dispatch
│   ├── subcontractor.py # Job accept/decline
│   └── admin.py         # History, archiving, code management
├── services/
│   ├── __init__.py
│   ├── access_codes.py  # Access code validation and registration
│   ├── jobs.py          # Job CRUD operations
│   └── archive.py       # Job archiving
└── utils/
    ├── __init__.py
    └── permissions.py   # Role-based access control
```

## Environment Variables (Required)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from @BotFather
- `DATABASE_URL` - PostgreSQL connection string
- `ADMIN_BOOTSTRAP_CODES` - Comma-separated admin access codes for initial setup
- `ARCHIVE_AFTER_DAYS` - Days before auto-archiving (default: 90)
- `LOG_LEVEL` - INFO/DEBUG/ERROR (default: INFO)
- `ENVIRONMENT` - development/production

## User Roles
- **Admin**: Manages the system, views history, creates access codes
- **Supervisor**: Creates and dispatches jobs
- **Subcontractor**: Receives and responds to jobs

## Commands
- `/start` - Start bot and authenticate with access code
- `/help` - Show available commands
- `/newjob` - Create new job (Supervisor)
- `/myjobs` - View created jobs (Supervisor)
- `/jobs` - View assigned jobs (Subcontractor)
- `/accept <id>` - Accept a job (Subcontractor)
- `/decline <id>` - Decline a job (Subcontractor)
- `/history` - View job history (Admin)
- `/archive` - Archive old jobs (Admin)
- `/createcode <code> <role>` - Create access code (Admin)

## Database
Uses PostgreSQL with SQLAlchemy async ORM.

## Recent Changes
- 2026-01-07: Full project structure created with all modules
