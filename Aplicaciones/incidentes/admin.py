# Aplicaciones/incidentes/admin.py
from django.contrib import admin
from .models import *

admin.site.register(TipoIncidente)
admin.site.register(Severidad)
admin.site.register(EstadoIncidente)
admin.site.register(TipoRecurso)
admin.site.register(EstadoRecurso)
admin.site.register(Incidente)
admin.site.register(Recurso)
admin.site.register(Asignacion)
admin.site.register(HistorialIncidente)
admin.site.register(AuditoriaAccion)

