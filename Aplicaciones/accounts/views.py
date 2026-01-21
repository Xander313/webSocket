from django.shortcuts import render
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .jwt import generar_tokens

from rest_framework.decorators import (api_view, permission_classes, parser_classes)
from rest_framework.permissions import IsAuthenticated
from Aplicaciones.accounts.permissions import (IsAdmin)
from django.contrib.auth.models import User
# Create your views here.



@api_view(["POST"])
def login_api(request):

    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if not user:
        return Response({"error": "Credenciales inválidas"}, status=401)

    rol = user.perfil.rol if hasattr(user, "perfil") else ""

    refresh = RefreshToken.for_user(user)

    refresh["role"] = rol
    refresh["email"] = user.email

    return Response({
        "user": user.username,
        "rol": rol,
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }
    })




@api_view(["POST"])
def logout_api(request):

    token = request.data.get("refresh")

    try:
        RefreshToken(token).blacklist()
        return Response({"ok":"logout"})
    except:
        return Response({"error":"token invalido"},status=400)
    



@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def usuarios_api(request):

    # LISTAR
    if request.method == "GET":

        qs = User.objects.select_related("perfil") \
            .exclude(id=request.user.id) \
            .exclude(perfil__rol="admin")
        data = []
        for u in qs:
            data.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "rol": u.perfil.rol,
                "activo": u.is_active
            })

        return Response(data)

    # CREAR
    if request.method == "POST":

        if User.objects.filter(username=request.data["username"]).exists():
            return Response(
                {"error": "El usuario ya existe"},
                status=400
            )

        user = User.objects.create_user(
            username=request.data["username"],
            email=request.data.get("email"),
            password=request.data["password"]
        )

        user.perfil.rol = request.data["rol"]
        user.perfil.save()

        return Response({"ok": "usuario creado"}, status=201)




@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def usuario_detalle_api(request, pk):

    try:
        user = User.objects.select_related("perfil").get(pk=pk)
    except User.DoesNotExist:
        return Response({"error":"No existe"}, status=404)

    # 🔒 PROTECCIÓN: no permitir desactivar a sí mismo
    if request.user.id == user.id:
        return Response(
            {"error": "No puedes desactivar tu propia cuenta"},
            status=403
        )

    # EDITAR / REACTIVAR
    if request.method == "PUT":

        user.is_active = request.data.get("activo", user.is_active)
        user.save()

        if "rol" in request.data:
            user.perfil.rol = request.data["rol"]
            user.perfil.save()

        return Response({"ok":"actualizado"})

    # DESACTIVAR
    if request.method == "DELETE":

        user.is_active = False
        user.save()

        return Response({"ok":"desactivado"})
