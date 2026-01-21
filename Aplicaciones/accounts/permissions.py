from rest_framework.permissions import BasePermission

# =========================
# PERMISOS POR ROL
# =========================

class IsAdmin(BasePermission):
    message = "Solo administradores pueden acceder a este recurso"

    def has_permission(self, request, view):

        # 1. Verificar que exista token
        if not request.auth:
            return False

        # 2. Leer rol desde claims
        role = request.auth.get("role")

        return role == "admin"


class IsOperador(BasePermission):
    def has_permission(self, request, view):
        message = "Solo operadores pueden acceder a este recurso"


        if not request.auth:
            return False

        role = request.auth.get("role")

        return role == "operador"


class IsAuditor(BasePermission):
    message = "Solo auditores pueden acceder a este recurso"

    def has_permission(self, request, view):

        if not request.auth:
            return False

        role = request.auth.get("role")

        return role == "auditor"


# =========================
# PERMISOS COMBINADOS
# =========================

class IsAdminOrOperador(BasePermission):
    def has_permission(self, request, view):

        if not request.auth:
            return False

        role = request.auth.get("role")

        return role in ["admin", "operador"]


class IsAdminOrAuditor(BasePermission):
    def has_permission(self, request, view):

        if not request.auth:
            return False

        role = request.auth.get("role")

        return role in ["admin", "auditor"]
