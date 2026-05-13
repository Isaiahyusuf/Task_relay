from src.bot.database.models import UserRole

# Higher number means higher privilege.
ROLE_LEVEL = {
    UserRole.SUBCONTRACTOR: 1,
    UserRole.SUPERVISOR: 2,
    UserRole.ADMIN: 3,
    UserRole.SUPER_ADMIN: 4,
}

ROLE_DISPLAY_NAME = {
    UserRole.SUPER_ADMIN: "General Manager",
    UserRole.ADMIN: "Manager",
    UserRole.SUPERVISOR: "Supervisor",
    UserRole.SUBCONTRACTOR: "Subcontractor",
}


def has_minimum_role(user_role: UserRole | None, minimum_role: UserRole) -> bool:
    if not user_role:
        return False
    return ROLE_LEVEL.get(user_role, 0) >= ROLE_LEVEL.get(minimum_role, 0)


def can_manage_role(manager_role: UserRole | None, target_role: UserRole) -> bool:
    if not manager_role:
        return False
    return ROLE_LEVEL.get(manager_role, 0) > ROLE_LEVEL.get(target_role, 0)


def creatable_roles(creator_role: UserRole | None) -> list[UserRole]:
    if creator_role == UserRole.SUPER_ADMIN:
        return [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.SUBCONTRACTOR]
    if creator_role == UserRole.ADMIN:
        return [UserRole.SUPERVISOR, UserRole.SUBCONTRACTOR]
    if creator_role == UserRole.SUPERVISOR:
        return [UserRole.SUBCONTRACTOR]
    return []


def role_display_name(role: UserRole | None) -> str:
    if not role:
        return "Unknown"
    return ROLE_DISPLAY_NAME.get(role, role.value.replace("_", " ").title())
