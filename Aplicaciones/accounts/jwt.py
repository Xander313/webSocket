from rest_framework_simplejwt.tokens import RefreshToken

def generar_tokens(user):
    refresh = RefreshToken.for_user(user)

    refresh["role"] = user.perfil.rol
    refresh["email"] = user.email

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    }
