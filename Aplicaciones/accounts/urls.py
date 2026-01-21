from django.urls import path
from .views import login_api,logout_api, usuarios_api, usuario_detalle_api
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("login/", login_api),
    path("refresh/", TokenRefreshView.as_view()),
    path("logout/", logout_api),


    path("usuarios/", usuarios_api),
    path("usuarios/<int:pk>/", usuario_detalle_api),

]
