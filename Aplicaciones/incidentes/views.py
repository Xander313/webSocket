from rest_framework.decorators import (
    api_view, permission_classes, parser_classes
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from Aplicaciones.accounts.permissions import (
    IsAdmin, IsOperador, IsAuditor, IsAdminOrOperador
)

from .models import *
from .serializers import *

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.deletion import ProtectedError


# ---------------- CATÁLOGOS ----------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def tipo_incidente_api(request):

    if request.method == "GET":
        qs = TipoIncidente.objects.all()
        return Response(TipoIncidenteSerializer(qs, many=True).data)

    if request.method == "POST":

        # solo admin crea (opcional)
        if request.auth["role"] != "admin":
            return Response({"detail":"Solo admin"}, status=403)

        ser = TipoIncidenteSerializer(data=request.data)

        if ser.is_valid():
            obj = ser.save()

            # 🔔 evento realtime
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                "catalogos",
                {
                    "type": "enviar_evento",
                    "data": {
                        "accion": "catalogo_actualizado",
                        "tabla": "tipo_incidente"
                    }
                }
            )

            return Response(ser.data, status=201)

        return Response(ser.errors, status=400)




# ---------------- SEVERIDAD ----------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def severidad_api(request):

    # LISTAR
    if request.method == "GET":
        qs = Severidad.objects.all()
        return Response(
            SeveridadSerializer(qs, many=True).data
        )

    # CREAR
    if request.method == "POST":

        # solo admin
        if request.auth["role"] != "admin":
            return Response({"detail":"Solo admin"}, status=403)

        ser = SeveridadSerializer(data=request.data)

        if ser.is_valid():
            obj = ser.save()

            # 🔔 evento realtime
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                "catalogos",
                {
                    "type": "enviar_evento",
                    "data": {
                        "accion": "catalogo_actualizado",
                        "tabla": "severidad"
                    }
                }
            )

            return Response(ser.data, status=201)

        return Response(ser.errors, status=400)



# ---------------- ESTADO INCIDENTE ----------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def estado_incidente_api(request):

    # LISTAR
    if request.method == "GET":
        qs = EstadoIncidente.objects.all()
        return Response(
            EstadoIncidenteSerializer(qs, many=True).data
        )

    # CREAR
    if request.method == "POST":

        # solo admin
        if request.auth["role"] != "admin":
            return Response({"detail":"Solo admin"}, status=403)

        ser = EstadoIncidenteSerializer(data=request.data)

        if ser.is_valid():
            obj = ser.save()

            # 🔔 evento realtime
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                "catalogos",
                {
                    "type": "enviar_evento",
                    "data": {
                        "accion": "catalogo_actualizado",
                        "tabla": "estado_incidente"
                    }
                }
            )

            return Response(ser.data, status=201)

        return Response(ser.errors, status=400)


# ---------------- INCIDENTES ----------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
@parser_classes([MultiPartParser, FormParser])
def incidentes_api(request):

    # LISTAR
    if request.method == "GET":
        qs = Incidente.objects.all()
        return Response(
            IncidenteSerializer(
                qs, many=True, context={"request": request}
            ).data
        )

    # CREAR
    if request.method == "POST":

        # solo operador puede crear
        if request.auth["role"] not in ["operador", "admin"]:

            return Response(
                {"detail": "Solo asministrador u operadores pueden crear incidentes"},
                status=403
            )

        ser = IncidenteSerializer(
            data=request.data,
            context={"request": request}
        )

        if ser.is_valid():

            incidente = ser.save(creado_por=request.user)

            # 🔔 EVENTO TIEMPO REAL (admin + operador)
            channel_layer = get_channel_layer()

            for grupo in ["rol_operador", "rol_admin"]:
                async_to_sync(channel_layer.group_send)(
                    grupo,
                    {
                        "type": "enviar_evento",
                        "data": {
                            "accion": "incidente_creado",
                            "id": incidente.id,
                            "tipo": incidente.tipo.nombre,
                            "severidad": incidente.severidad.nombre,
                            "lat": str(incidente.latitud),
                            "lng": str(incidente.longitud)
                        }
                    }
                )

            return Response(
                IncidenteSerializer(
                    incidente, context={"request": request}
                ).data,
                status=201
            )

        return Response(ser.errors, status=400)

@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def incidente_detalle_api(request, pk):

    try:
        inc = Incidente.objects.get(pk=pk)
    except Incidente.DoesNotExist:
        return Response(
            {"detail": "No existe"},
            status=404
        )

    # GET
    if request.method == "GET":
        return Response(
            IncidenteSerializer(
                inc, context={"request": request}
            ).data
        )

    # PUT / PATCH
    if request.method in ["PUT", "PATCH"]:

        # SOLO operador
        if request.auth["role"] not in ["operador", "admin"]:
            return Response(
                {"detail": "Solo operadores o administrador"},
                status=403
            )

        ser = IncidenteSerializer(
            inc,
            data=request.data,
            partial=True,   # PATCH
            context={"request": request}
        )

        if ser.is_valid():
            ser.save()
            return Response(ser.data)

        return Response(ser.errors, status=400)

    # DELETE (opcional)
    if request.method == "DELETE":

        inc.delete()
        return Response(status=204)





# ---------------- CAMBIAR ESTADO ----------------

@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def cambiar_estado(request, pk):

    try:
        inc = Incidente.objects.get(pk=pk)
    except Incidente.DoesNotExist:
        return Response(
            {"detail": "Incidente no encontrado"},
            status=404
        )

    inc.estado_id = request.data.get("estado")
    inc.save()

    # 🔔 EVENTO TIEMPO REAL (todos)
    channel_layer = get_channel_layer()

    for grupo in [
        "rol_admin", "rol_operador",
        "rol_rescatista", "rol_auditor"
    ]:
        async_to_sync(channel_layer.group_send)(
            grupo,
            {
                "type": "enviar_evento",
                "data": {
                    "accion": "estado_actualizado",
                    "incidente": inc.id,
                    "nuevo_estado": inc.estado.nombre
                }
            }
        )

    # historial automático
    HistorialIncidente.objects.create(
        incidente=inc,
        estado=inc.estado,
        usuario=request.user,
        observacion="Cambio de estado"
    )

    return Response({"ok": "estado actualizado"})


# ---------------- RECURSOS ----------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def recursos_api(request):

    if request.method == "GET":
        qs = Recurso.objects.all()
        return Response(
            RecursoSerializer(qs, many=True).data
        )

    if request.method == "POST":
        ser = RecursoSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=201)
        return Response(ser.errors, status=400)


# ---------------- ASIGNACIÓN ----------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOperador])
def asignar_recurso(request):

    ser = AsignacionSerializer(data=request.data)

    if ser.is_valid():

        asignacion = ser.save()

        # 🔔 EVENTO TIEMPO REAL (solo rescatista)
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "rol_rescatista",
            {
                "type": "enviar_evento",
                "data": {
                    "accion": "recurso_asignado",
                    "incidente": asignacion.incidente.id,
                    "recurso": asignacion.recurso.nombre
                }
            }
        )

        return Response(ser.data, status=201)

    return Response(ser.errors, status=400)


# ---------------- AUDITOR ----------------

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAuditor])
def historial_incidente(request, pk):

    qs = HistorialIncidente.objects.filter(
        incidente_id=pk
    )

    return Response({
        "mensaje": "Endpoint activo",
        "total": qs.count()
    })



@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def tipo_incidente_detalle(request, pk):

    try:
        obj = TipoIncidente.objects.get(pk=pk)
    except:
        return Response(status=404)

    if request.method == "PUT":
        ser = TipoIncidenteSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)

    if request.method == "DELETE":
        obj.delete()
        return Response(status=204)


@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def severidad_detalle(request, pk):

    try:
        obj = Severidad.objects.get(pk=pk)
    except:
        return Response(status=404)

    if request.method == "PUT":
        ser = SeveridadSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)

    if request.method == "DELETE":
        obj.delete()
        return Response(status=204)



@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def estado_incidente_detalle(request, pk):

    try:
        obj = EstadoIncidente.objects.get(pk=pk)
    except:
        return Response(status=404)

    if request.method == "PUT":
        ser = EstadoIncidenteSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)

    if request.method == "DELETE":
        obj.delete()
        return Response(status=204)



@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOperador])
def asignar_recursos(request, pk):

    recursos = request.data.get("recursos")

    if not recursos:
        return Response({"error":"No hay recursos"}, status=400)

    inc = Incidente.objects.get(pk=pk)

    for r in recursos:

        Asignacion.objects.create(
            incidente=inc,
            recurso_id=r
        )

        Recurso.objects.filter(id=r).update(
            estado_id=2  
        )

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "rol_rescatista",
        {
            "type":"enviar_evento",
            "data":{
                "accion":"recurso_asignado",
                "incidente": inc.id
            }
        }
    )

    return Response({"ok":"recursos asignados"})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOperador])
def recursos_disponibles(request):

    qs = Recurso.objects.filter(estado__nombre="Disponible")

    return Response(
        RecursoSerializer(qs, many=True).data
    )



@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def tipo_recurso_api(request):

    # LISTAR
    if request.method == "GET":
        qs = TipoRecurso.objects.all()
        return Response(
            TipoRecursoSerializer(qs, many=True).data
        )

    # CREAR
    if request.method == "POST":

        ser = TipoRecursoSerializer(data=request.data)

        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=201)

        return Response(ser.errors, status=400)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def estado_recurso_api(request):

    # LISTAR
    if request.method == "GET":
        qs = EstadoRecurso.objects.all()
        return Response(
            EstadoRecursoSerializer(qs, many=True).data
        )

    # CREAR
    if request.method == "POST":

        ser = EstadoRecursoSerializer(data=request.data)

        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=201)

        return Response(ser.errors, status=400)


@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def recurso_detalle(request, pk):

    try:
        obj = Recurso.objects.get(pk=pk)
    except:
        return Response(status=404)

    # EDITAR
    if request.method == "PUT":

        ser = RecursoSerializer(
            obj,
            data=request.data,
            partial=True
        )

        if ser.is_valid():
            ser.save()
            return Response(ser.data)

        return Response(ser.errors, status=400)

    # ELIMINAR
    if request.method == "DELETE":

        obj.soft_delete()   # usando tu soft delete
        return Response(status=204)



# ---------------- TIPO RECURSO ----------------

@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def tipo_recurso_detalle(request, pk):

    try:
        obj = TipoRecurso.objects.get(pk=pk)
    except:
        return Response({"error":"No existe"}, status=404)

    # EDITAR
    if request.method == "PUT":

        ser = TipoRecursoSerializer(
            obj,
            data=request.data,
            partial=True
        )

        if ser.is_valid():
            ser.save()
            return Response(ser.data)

        return Response(ser.errors, status=400)

    # ELIMINAR
    if request.method == "DELETE":

        try:
            obj.delete()
            return Response(status=204)

        except ProtectedError:

            return Response({
                "error":"No se puede eliminar porque está en uso"
            }, status=409)


# ---------------- ESTADO RECURSO ----------------

@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def estado_recurso_detalle(request, pk):

    try:
        obj = EstadoRecurso.objects.get(pk=pk)
    except:
        return Response({"error":"No existe"}, status=404)

    # EDITAR
    if request.method == "PUT":

        ser = EstadoRecursoSerializer(
            obj,
            data=request.data,
            partial=True
        )

        if ser.is_valid():
            ser.save()
            return Response(ser.data)

        return Response(ser.errors, status=400)

    # ELIMINAR
    if request.method == "DELETE":

        try:
            obj.delete()
            return Response(status=204)

        except ProtectedError:

            return Response({
                "error":"No se puede eliminar porque está en uso"
            }, status=409)
