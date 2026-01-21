"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.urls import path
from .views import *



urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("Aplicaciones.accounts.urls")),
    path("api/", include("Aplicaciones.incidentes.urls")),
    path("", login_view, name="login"),
    path("adm/panel/", usuarios_admin, name="admin-panel"),
    path("adm/catalogo/", catalogos_admin, name="admin-catalogo"),
    path("oper/incidente/", operador_icidente, name="operador_icidente"),





]
