# TaskRelay Bot

## Overview
TaskRelay Bot is a Telegram-based workflow automation system for managing job assignments between Supervisors, Subcontractors, and Admins. Features a user-friendly button-based interface and is ready for Railway deployment.

## Project Structure
```
src/bot/
├── main.py              # Entry point with graceful shutdown
├── config.py            # Environment configuration & validation
├── database/
│   ├── __init__.py
│   ├── models.py        # SQLAlchemy models (User, Job, AccessCode, Team)
│   └── session.py       # Database session with Railway SSL support
├── handlers/
│   ├── __init__.py
│   ├── auth.py          # Authentication with role-based menus
│   ├── supervisor.py    # Job creation with inline buttons
│   ├── subcontractor.py # Job accept/decline with buttons
│   └── admin.py         # History, archiving, code management
├── services/
│   ├── __init__.py
│   ├── access_codes.py  # Access code validation and registration
│   ├── jobs.py          # Job CRUD operations
│   └── archive.py       # Job archiving (90-day auto-archive)
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
- `ARCHIVE_AFTER_DAYS` - Days before auto-archiving (default: 90)
- `LOG_LEVEL` - INFO/DEBUG/ERROR (default: INFO)
- `ENVIRONMENT` - development/production

## User Roles
- **Admin**: Manages the system, views history, creates access codes
- **Supervisor**: Creates and dispatches jobs
- **Subcontractor**: Receives and responds to jobs

## Features
- **Button-based UI**: Reply keyboards for main menu, inline keyboards for all actions
- **Role-based menus**: Different menu options based on user role
- **Job workflow**: Create → Dispatch → Accept/Decline with quote support
- **Pagination**: Paginated job lists for history viewing
- **Error handling**: Global error handler with user-friendly messages
- **Graceful shutdown**: Proper cleanup on SIGTERM/SIGINT

## Railway Deployment
1. Connect your GitHub repository to Railway
2. Add PostgreSQL plugin
3. Set environment variables in Railway dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `ADMIN_BOOTSTRAP_CODES`
   - `ENVIRONMENT=production`
4. Railway will use `railway.toml` configuration automatically

## Commands by Role

### All Users
- `/start` - Start bot and authenticate
- `/help` - Show available commands

### Admin (Button Menu)
- 📊 Job History - View all job records
- 📦 Archive Jobs - Archive old completed jobs
- 🔑 Create Access Code - Generate new access codes
- 📋 View Archived - Browse archived jobs

### Supervisor (Button Menu)
- ➕ New Job - Create and dispatch a new job
- 📋 My Jobs - View jobs you've created

### Subcontractor (Button Menu)
- 📋 My Assigned Jobs - View jobs assigned to you
- ✅ Accept / ❌ Decline buttons on each job

## Database
Uses PostgreSQL with SQLAlchemy async ORM. Supports Railway PostgreSQL with SSL.

## Recent Changes
- 2026-01-07: Fixed context-aware pagination (page:sup, page:history, page:archived) to prevent cross-role data contamination
- 2026-01-07: Added view_job handlers with context tokens for all roles
- 2026-01-07: Added back navigation for all list views (back:sup, back:history, back:archived)
- 2026-01-07: Added user-friendly button interface throughout
- 2026-01-07: Added Railway deployment configuration
- 2026-01-07: Added production error handling and graceful shutdown
- 2026-01-07: Added pagination for job lists
- 2026-01-07: Full project structure created with all modules
