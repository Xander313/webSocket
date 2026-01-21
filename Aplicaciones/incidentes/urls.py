from django.urls import path
from .views import *
urlpatterns = [

    # CATÁLOGOS
    path("catalogos/tipo-incidente/", tipo_incidente_api),
    path("catalogos/severidad/", severidad_api),        
    path("catalogos/estado-incidente/", estado_incidente_api),  
    path("catalogos/tipo-incidente/<int:pk>/", tipo_incidente_detalle),
    path("catalogos/severidad/<int:pk>/", severidad_detalle),
    path("catalogos/estado-incidente/<int:pk>/", estado_incidente_detalle),
    path("catalogos/tipo-recurso/<int:pk>/", tipo_recurso_detalle),
    path("catalogos/estado-recurso/<int:pk>/", estado_recurso_detalle),




    path("catalogos/tipo-recurso/", tipo_recurso_api),
    path("catalogos/estado-recurso/", estado_recurso_api),

    path("recursos/", recursos_api),
    path("recursos/<int:pk>/", recurso_detalle),



    # INCIDENTES
    path("incidentes/", incidentes_api),
    path("incidentes/<int:pk>/", incidente_detalle_api),

    path("incidentes/<int:pk>/estado/", cambiar_estado),

    path("incidentes/<int:pk>/asignar/", asignar_recursos),

    


    # RECURSOS
    path("recursos/", recursos_api),

    path("recursos/disponibles/", recursos_disponibles),



    # ASIGNACIONES
    path("asignar/", asignar_recurso),

    # AUDITOR
    path("historial/<int:pk>/", historial_incidente),
]
