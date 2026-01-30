# TaskRelay Bot

## Overview
TaskRelay Bot is a Telegram-based workflow automation system for managing job assignments between Supervisors, Subcontractors, and Admins. Features a complete button-based interface, job lifecycle management, quote system, and automated reminders.

## Project Structure
```
src/bot/
├── main.py              # Entry point with scheduler and graceful shutdown
├── config.py            # Environment configuration & validation
├── database/
│   ├── __init__.py
│   ├── models.py        # SQLAlchemy models (User, Job, AccessCode, Team, Quote)
│   └── session.py       # Database session with Railway SSL support
├── handlers/
│   ├── __init__.py
│   ├── auth.py          # Authentication with role-based menus
│   ├── supervisor.py    # Job creation, quote management, job actions
│   ├── subcontractor.py # Job accept/decline, start/complete, availability
│   └── admin.py         # History, archiving, code management
├── services/
│   ├── __init__.py
│   ├── access_codes.py  # Access code validation and registration
│   ├── jobs.py          # Job CRUD operations
│   ├── quotes.py        # Quote submission and acceptance
│   ├── availability.py  # Subcontractor availability management
│   ├── archive.py       # Job archiving (90-day auto-archive)
│   └── scheduler.py     # Background reminders and auto-close
├── middleware/
│   ├── __init__.py
│   └── error_handler.py # Global error handling
└── utils/
    ├── __init__.py
    ├── permissions.py   # Role-based access control decorators
    └── keyboards.py     # Inline/reply keyboard builders
```

## Environment Variables (Required)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from @BotFather
- `DATABASE_URL` - PostgreSQL connection string
- `ADMIN_BOOTSTRAP_CODES` - Comma-separated admin access codes for initial setup
- `SUPER_ADMIN_CODE` - Secret code for super admin access (changing this invalidates current super admin)
- `ARCHIVE_AFTER_DAYS` - Days before auto-archiving (default: 90)
- `RESPONSE_REMINDER_HOURS` - Hours before sending job reminder (default: 24)
- `JOB_AUTO_CLOSE_HOURS` - Hours before auto-cancelling unanswered jobs (default: 72)
- `LOG_LEVEL` - INFO/DEBUG/ERROR (default: INFO)
- `ENVIRONMENT` - development/production

## User Roles
- **Admin**: Manages the system, views history, creates access codes
- **Supervisor**: Creates jobs, manages quotes, tracks job progress
- **Subcontractor**: Receives jobs, submits quotes, marks jobs complete

## Job Status Lifecycle
1. **CREATED** - Job created but not sent
2. **SENT** - Job sent to subcontractor(s)
3. **ACCEPTED** - Subcontractor accepted the job
4. **IN_PROGRESS** - Work has started
5. **COMPLETED** - Job marked as complete
6. **CANCELLED** - Job cancelled by supervisor or auto-closed
7. **ARCHIVED** - Old job archived for records

## Features

### Supervisor Dashboard
- **My Jobs** - View all jobs
- **Pending Jobs** - Jobs awaiting response (CREATED, SENT)
- **Active Jobs** - Jobs in progress (ACCEPTED, IN_PROGRESS)
- **View Quotes** - Compare quotes for quote jobs
- **Accept Quote** - Select winning quote
- **Cancel Job** - Cancel unstarted jobs
- **Mark Complete** - Close completed jobs

### Subcontractor Features
- **Available Jobs** - View jobs waiting for response
- **My Active Jobs** - View accepted/in-progress jobs
- **Start Job** - Begin work on accepted job
- **Mark Complete** - Finish job
- **Availability Toggle** - Set status (Available/Busy/Away)

### Quote System
- Subcontractors submit quotes for quote-type jobs
- Supervisors view all quotes with amounts and timestamps
- Accept quote assigns job to winning subcontractor
- Other subcontractors notified when job closes

### Automated Features
- **Reminders** - Notify subcontractors after RESPONSE_REMINDER_HOURS
- **Auto-Close** - Cancel unanswered jobs after JOB_AUTO_CLOSE_HOURS
- **Auto-Archive** - Archive completed jobs after ARCHIVE_AFTER_DAYS

## Railway Deployment
1. Connect your GitHub repository to Railway
2. Add PostgreSQL plugin
3. Set environment variables in Railway dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `ADMIN_BOOTSTRAP_CODES`
   - `ENVIRONMENT=production`
4. Railway will use `railway.toml` configuration automatically

## Database
Uses PostgreSQL with SQLAlchemy async ORM. Supports Railway PostgreSQL with SSL.

### Tables
- `users` - User accounts with roles and availability
- `jobs` - Job records with full lifecycle tracking
- `quotes` - Quote submissions for quote-type jobs
- `access_codes` - Registration codes by role
- `teams` - Team groupings for users and jobs

## Teams
Subcontractors are organized into two teams:
- **Northwest Team** - 🌲 Subcontractors in the Northwest region
- **Southeast Team** - ☀️ Subcontractors in the Southeast region

### Team Assignment
- When creating access codes for Admins, Supervisors, or Subcontractors, the creator must select which team they will belong to
- The team assignment flows from top to bottom: Super Admin → Admin → Supervisor → Subcontractor
- The team assignment is automatic when the user registers with that code
- Only Super Admins are not assigned to a team (they have access to everything)

### Job Sending Options
When supervisors create jobs, they can choose:
- **Bot-Wide** - Send to ALL available subcontractors from both teams
- **Northwest Team Only** - Send only to Northwest Team members
- **Southeast Team Only** - Send only to Southeast Team members
- **Save as Draft** - Save without sending

## Recent Changes
- 2026-01-30: Added team system - Northwest and Southeast teams
- 2026-01-30: Supervisors can now send jobs to specific teams or bot-wide
- 2026-01-30: Access codes for subcontractors require team selection
- 2026-01-29: Subcontractors must provide company name when accepting jobs
- 2026-01-29: Added SUPER_ADMIN role with full access to delete any user including admins
- 2026-01-29: Added job submission flow - subcontractors submit with notes and photo proof
- 2026-01-29: Added SUBMITTED job status - supervisors review submissions before marking complete
- 2026-01-29: Removed team restrictions - any subcontractor can now see and accept any job bot-wide
- 2026-01-29: Added notifications for job creation (all available subs) and acceptance (supervisor)
- 2026-01-29: Added 'Mark Done' button for subcontractors to notify supervisors for investigation
- 2026-01-07: Added complete job lifecycle (CREATED → SENT → ACCEPTED → IN_PROGRESS → COMPLETED)
- 2026-01-07: Added Quote model and quote comparison view for supervisors
- 2026-01-07: Added subcontractor availability toggle (Available/Busy/Away)
- 2026-01-07: Added background scheduler for reminders and auto-close
- 2026-01-07: Added supervisor job dashboard with Pending/Active filters
- 2026-01-07: Added Start Job and Mark Complete buttons for subcontractors
- 2026-01-07: Fixed context-aware pagination for all list views
- 2026-01-07: Added Railway deployment configuration
