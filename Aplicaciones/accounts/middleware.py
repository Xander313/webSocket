import jwt
from django.conf import settings
from django.shortcuts import redirect

class JWTAuthMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        rutas_protegidas = (
            request.path.startswith("/adm") or
            request.path.startswith("/oper")
        )

        if rutas_protegidas:

            token = request.COOKIES.get("access")

            if not token:
                return redirect("/")

            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"]
                )

                request.user_role = payload.get("role")

            except:
                return redirect("/")

        return self.get_response(request)
