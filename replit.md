# TaskRelay Bot

## Overview

TaskRelay Bot is a Telegram-based workflow automation system designed to manage job assignments between Supervisors, Subcontractors, and Admins. The bot facilitates job creation, quote collection, acceptance/decline tracking, and supervisor-subcontractor communication. Access is controlled via secure access codes that automatically assign user roles and teams.

**Core functionality:**
- Job creation (quote-based and preset price)
- Quote submission and tracking
- Role-based access control (Supervisor, Subcontractor, Admin)
- Job history logging and archiving
- Real-time notifications between parties

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Framework**: aiogram (Python async Telegram bot framework)
- **Pattern**: Event-driven with command and message handlers
- **Async Runtime**: asyncio for non-blocking I/O operations

### Role-Based Access Control
- Three distinct roles: Supervisor, Subcontractor, Admin
- Access codes determine user roles and team assignments
- Each role has specific capabilities and command access

### Application Structure
- **Entry Point**: `main.py` handles bot initialization and polling
- **Configuration**: Environment variables for sensitive data (TELEGRAM_BOT_TOKEN)
- **Current State**: Skeleton implementation with placeholder handlers

### Data Requirements (To Be Implemented)
The system will need to persist:
- User registrations with roles and team assignments
- Job records with status tracking
- Quote submissions
- Job history for archival purposes

### Workflow Patterns
- **Job Creation Flow**: Supervisor creates job → System notifies subcontractors → Subcontractor responds → Supervisor notified
- **Quote Flow**: Supervisor requests quote → Subcontractor submits price → Supervisor reviews

## External Dependencies

### Telegram Bot API
- **Purpose**: Core messaging and user interaction
- **Integration**: Via aiogram library
- **Authentication**: Bot token stored in TELEGRAM_BOT_TOKEN environment variable

### Python Packages
- **aiogram**: Async Telegram Bot API framework

### Required Secrets
- `TELEGRAM_BOT_TOKEN`: Telegram Bot API token from BotFather