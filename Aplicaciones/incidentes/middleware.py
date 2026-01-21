from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
import json
from .models import AuditoriaAccion


@database_sync_to_async
def get_user_from_token(token: str):
    try:
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AnonymousUser

        User = get_user_model()

        validated = AccessToken(token)
        user_id = validated.get("user_id")

        return User.objects.get(id=user_id)

    except Exception:
        from django.contrib.auth.models import AnonymousUser
        return AnonymousUser()


class JwtAuthMiddleware:

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):

        from django.contrib.auth.models import AnonymousUser

        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)

        token_list = params.get("token")

        if token_list:
            scope["user"] = await get_user_from_token(token_list[0])
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)




class AuditoriaMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        # Solo auditar métodos importantes
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return response

        # Solo si usuario autenticado
        if not request.user.is_authenticated:
            return response

        try:
            body = request.body.decode("utf-8")
            data = json.loads(body) if body else None
        except:
            data = None

        # Obtener IP real
        ip = request.META.get(
            "HTTP_X_FORWARDED_FOR",
            request.META.get("REMOTE_ADDR")
        )

        AuditoriaAccion.objects.create(
            usuario=request.user,
            rol=getattr(request.user.perfil, "rol", ""),
            accion=self.detectar_accion(request.method),
            metodo=request.method,
            endpoint=request.path,
            tabla=self.detectar_tabla(request.path),
            registro_id=self.detectar_id(request.path),
            ip=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            data=data
        )

        return response

    def detectar_accion(self, metodo):
        return {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE"
        }.get(metodo, "OTHER")

    def detectar_tabla(self, path):
        if "incidentes" in path:
            return "incidente"
        if "recursos" in path:
            return "recurso"
        if "asignar" in path:
            return "asignacion"
        return "general"

    def detectar_id(self, path):
        try:
            return int(path.strip("/").split("/")[-1])
        except:
            return None
