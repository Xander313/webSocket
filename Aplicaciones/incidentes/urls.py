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

    path("catalogos/tipo-recurso/", tipo_recurso_api),
    path("catalogos/estado-recurso/", estado_recurso_api),

    path("catalogos/tipo-recurso/<int:pk>/", tipo_recurso_detalle),
    path("catalogos/estado-recurso/<int:pk>/", estado_recurso_detalle),

    # RECURSOS
    path("recursos/", recursos_api),
    path("recursos/<int:pk>/", recurso_detalle),
    path("recursos/disponibles/", recursos_disponibles),

    # INCIDENTES
    path("incidentes/", incidentes_api),
    path("incidentes/<int:pk>/", incidente_detalle_api),

    path("incidentes/<int:pk>/estado/", cambiar_estado),

    # ✅ Datos para modal de asignación (rescatistas + disponibles + asignados + tipos)
    path("incidentes/<int:pk>/asignaciones/", asignaciones_incidente_api),

    # ✅ Guardar asignación (rescatista + asignar/desasignar recursos)
    path("incidentes/<int:pk>/asignar/", asignar_recursos),


    path("incidentes/<int:pk>/auditoria/", auditoria_incidente),
    path("api/incidentes/inactivos/", incidentes_inactivos),




    # ASIGNACIONES directas (si lo usas aún)
    path("asignar/", asignar_recurso),



    # AUDITOR
    path("historial/<int:pk>/", historial_incidente),
]
