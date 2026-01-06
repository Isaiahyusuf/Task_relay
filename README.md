TaskRelay Bot is a Telegram-based workflow automation bot designed to manage job assignments between Supervisors, Subcontractors, and Admins.

The bot streamlines:
	•	Job creation
	•	Quote collection
	•	Acceptance/decline tracking
	•	Supervisor–subcontractor communication
	•	Job history logging and archiving

All access is controlled via secure access codes that automatically assign user roles and teams.

⸻

Core Roles

👷 Supervisor

Supervisors are responsible for creating and dispatching jobs.

Supervisor capabilities:
	•	Create Quote Jobs
	•	Create Preset Price Jobs
	•	Attach job details:
	•	Address
	•	Description
	•	Photos (optional)
	•	Price (for preset jobs)
	•	Send jobs to assigned subcontractors
	•	Receive notifications on job acceptance or decline

⸻

🧑‍🔧 Subcontractor

Subcontractors receive and respond to jobs.

Subcontractor capabilities:
	•	Receive job details
	•	Accept or decline jobs
	•	Submit quotes for quote-based jobs
	•	Automatically notify supervisors on action taken

⸻

🛠 Admin

Admins manage system oversight and records.

Admin capabilities:
	•	View full job history
	•	Track accepted and declined jobs
	•	Access job logs using commands
	•	Automatic archiving of jobs older than 3 months

⸻

Bot Workflow

1. Access Control
	•	User starts the bot
	•	Enters an access code
	•	Bot validates the code
	•	❌ Invalid code → Access denied
	•	✅ Valid code → Role & team assigned automatically

⸻

2. Job Creation (Supervisor)

Quote Job
Used when price is not fixed.

Steps:
	1.	Enter job address
	2.	Add job description
	3.	Upload photos (optional)
	4.	Mark job as complete
	5.	Send to subcontractors
	6.	Await quotes

Preset Job
Used when price is fixed.

Steps:
	1.	Enter job address
	2.	Add job description
	3.	Set fixed price
	4.	Send to subcontractors

⸻

3. Job Response (Subcontractor)

Upon receiving a job:
	•	✅ Accept Job
	•	❌ Decline Job

If the job is a quote job, subcontractor submits a quote after accepting.

⸻

4. Job Status Handling
	•	Accepted Job
	•	Supervisor is notified
	•	Job status updated
	•	Declined Job
	•	Decline is recorded
	•	Supervisor is notified

⸻

5. Admin History & Archiving
	•	/history command shows job history
	•	Jobs older than 3 months are auto-archived
	•	Archived jobs remain viewable but locked

⸻

Commands Summary

User
	•	/start – Start the bot
	•	/accept – Accept a job
	•	/decline – Decline a job

Admin
	•	/history – View job history
	•	/archive – Manual archive (optional)

⸻

Technical Notes
	•	Platform: Telegram Bot API
	•	Language: Python (Aiogram or python-telegram-bot)
	•	Database:
	•	SQLite (MVP)
	•	PostgreSQL (Production)
	•	Hosting:
	•	Replit (Development)
	•	VPS / Railway / Render (Production)

⸻

Security & Design Principles
	•	Role-based access control
	•	Access-code authentication
	•	Team-based job routing
	•	No subcontractor sees another subcontractor’s response
	•	Immutable job logs after archiving
