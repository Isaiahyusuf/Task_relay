from .auth import router as auth_router
from .supervisor import router as supervisor_router
from .subcontractor import router as subcontractor_router
from .admin import router as admin_router
from .safety_checklist import router as safety_checklist_router

__all__ = ['auth_router', 'supervisor_router', 'subcontractor_router', 'admin_router', 'safety_checklist_router']
