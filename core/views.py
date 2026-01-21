from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

API_LOGIN = "http://127.0.0.1:8000/api/login/"

def login_view(request):
    return render(request, "login.html")


def usuarios_admin(request):

    if request.user_role != "admin":
        return redirect("/")

    return render(request, "administrador/usuarios.html")


def catalogos_admin(request):

    if request.user_role != "admin":
        return redirect("/")

    return render(request, "administrador/catalogos.html")




def operador_icidente(request):

    if request.user_role != "operador":
        return redirect("/")

    return render(request, "operador/incidentes.html")