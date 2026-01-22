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

from django.contrib.auth.models import User, Group
from django.db.models.deletion import ProtectedError

from .models import *
from .serializers import *

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone


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
            ser.save()

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


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def severidad_api(request):

    if request.method == "GET":
        qs = Severidad.objects.all()
        return Response(SeveridadSerializer(qs, many=True).data)

    if request.method == "POST":

        if request.auth["role"] != "admin":
            return Response({"detail":"Solo admin"}, status=403)

        ser = SeveridadSerializer(data=request.data)

        if ser.is_valid():
            ser.save()

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


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def estado_incidente_api(request):

    if request.method == "GET":
        qs = EstadoIncidente.objects.all()
        return Response(EstadoIncidenteSerializer(qs, many=True).data)

    if request.method == "POST":

        if request.auth["role"] != "admin":
            return Response({"detail":"Solo admin"}, status=403)

        ser = EstadoIncidenteSerializer(data=request.data)

        if ser.is_valid():
            ser.save()

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

    # ================= GET =================
    if request.method == "GET":

        hoy = timezone.now().date()

        # todos (activos + inactivos) pero <= hoy
        fecha = request.GET.get("fecha")

        qs = Incidente.all_objects.all()

        if fecha:
            qs = qs.filter(fecha_creacion__date__lte=fecha)
        else:
            qs = qs.filter(
                fecha_creacion__date__lte=timezone.now().date()
            )


        return Response(
            IncidenteSerializer(
                qs,
                many=True,
                context={"request": request}
            ).data
        )


    # ================= POST =================
    if request.method == "POST":

        if request.auth["role"] not in ["operador", "admin"]:
            return Response(
                {"detail": "Solo administrador u operadores pueden crear incidentes"},
                status=403
            )

        data = request.data.copy()

        if not data.get("estado"):
            data["estado"] = 1

        ser = IncidenteSerializer(data=data, context={"request": request})

        if ser.is_valid():

            incidente = ser.save(
                creado_por=request.user,
                activo=True
            )

            # 🔔 realtime
            channel_layer = get_channel_layer()

            for grupo in ["rol_operador", "rol_admin"]:
                async_to_sync(channel_layer.group_send)(
                    grupo,
                    {
                        "type": "enviar_evento",
                        "data": {
                            "accion": "incidente_update"
                        }
                    }
                )

            return Response(
                IncidenteSerializer(
                    incidente,
                    context={"request": request}
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
        return Response({"detail": "No existe"}, status=404)

    if request.method == "GET":
        return Response(IncidenteSerializer(inc, context={"request": request}).data)

    if request.method in ["PUT", "PATCH"]:

        if request.auth["role"] not in ["operador", "admin"]:
            return Response({"detail": "Solo operadores o administrador"}, status=403)

        ser = IncidenteSerializer(
            inc,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if ser.is_valid():
            ser.save()
            return Response(ser.data)

        return Response(ser.errors, status=400)

    if request.method == "DELETE":

        # 🔥 liberar antes de borrar
        liberar_recursos_incidente(inc)

        inc.soft_delete()

        channel_layer = get_channel_layer()
        for grupo in ["rol_admin", "rol_operador", "rol_rescatista", "rol_auditor"]:
            async_to_sync(channel_layer.group_send)(
                grupo,
                {
                    "type":"enviar_evento",
                    "data":{
                        "accion":"incidente_update"
                    }
                }
            )

        return Response(status=204)



# ---------------- CAMBIAR ESTADO ----------------

@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def cambiar_estado(request, pk):

    try:
        inc = Incidente.objects.get(pk=pk)
    except Incidente.DoesNotExist:
        return Response({"detail": "Incidente no encontrado"}, status=404)

    try:
        nuevo_estado = int(request.data.get("estado"))
    except:
        return Response({"error":"Estado inválido"}, status=400)

    inc.estado_id = nuevo_estado
    inc.save()


    estado_cerrado = EstadoIncidente.objects.filter(
        nombre__iexact="Cerrado"
    ).first()

    if estado_cerrado and nuevo_estado == estado_cerrado.id:
        liberar_recursos_incidente(inc)


    # 🔔 EVENTO TIEMPO REAL (todos)
    channel_layer = get_channel_layer()

    for grupo in ["rol_admin", "rol_operador", "rol_rescatista", "rol_auditor"]:
        async_to_sync(channel_layer.group_send)(
            grupo,
            {
                "type": "enviar_evento",
                "data": {
                    "accion": "incidente_update"
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
# ✅ GET también para operador (para consultas). POST sigue siendo solo admin.
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def recursos_api(request):

    if request.method == "GET":
        qs = Recurso.objects.all()
        return Response(RecursoSerializer(qs, many=True).data)

    if request.method == "POST":
        if request.auth["role"] != "admin":
            return Response({"detail":"Solo admin"}, status=403)

        ser = RecursoSerializer(data=request.data)
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

    if request.method == "DELETE":
        obj.soft_delete()
        return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOperador])
def recursos_disponibles(request):

    qs = Recurso.objects.filter(estado__nombre__iexact="Disponible")
    return Response(RecursoSerializer(qs, many=True).data)


# ---------------- ASIGNACIÓN (legacy) ----------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOperador])
def asignar_recurso(request):

    ser = AsignacionSerializer(data=request.data)

    if ser.is_valid():

        asignacion = ser.save()

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


# ---------------- MODAL ASIGNACIÓN: DATOS ----------------
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def asignaciones_incidente_api(request, pk):
    '''
    Devuelve todo lo necesario para el modal:
    - rescatistas (usuarios con rol/grupo rescatista)
    - tipos_recurso (para filtro)
    - disponibles (recursos estado=Disponible)
    - asignados (recursos ya asignados al incidente)
    - rescatista_actual (incidente.rescatista_id)
    '''

    try:
        inc = Incidente.objects.get(pk=pk)
    except Incidente.DoesNotExist:
        return Response({"detail":"Incidente no encontrado"}, status=404)

    # 1) Rescatistas: por Group "rescatista" (ajusta si tu modelo de roles es distinto)
    rescatistas_qs = User.objects.filter(
        perfil__rol__iexact="rescatista"
    )
    rescatistas = [
        {
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name
        } for u in rescatistas_qs
    ]

    # 2) Tipos de recurso (filtro)
    tipos = TipoRecurso.objects.all()
    tipos_data = TipoRecursoSerializer(tipos, many=True).data

    # 3) Recursos asignados (activos) para este incidente
    asignaciones = Asignacion.objects.filter(incidente=inc, activo=True).select_related("recurso", "recurso__tipo", "recurso__estado")
    asignados_recursos = [a.recurso for a in asignaciones]
    asignados_data = RecursoSerializer(asignados_recursos, many=True).data

    # 4) Disponibles
    disponibles_qs = Recurso.objects.filter(estado__nombre__iexact="Disponible")
    disponibles_data = RecursoSerializer(disponibles_qs, many=True).data

    return Response({
        "incidente": inc.id,
        "rescatista_actual": inc.rescatista_id,
        "rescatistas": rescatistas,
        "tipos_recurso": tipos_data,
        "disponibles": disponibles_data,
        "asignados": asignados_data
    })


# ---------------- GUARDAR ASIGNACIÓN (rescatista + recursos) ----------------
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOperador])
def asignar_recursos(request, pk):
    '''
    Body:
    {
      "rescatista": 5 | null,
      "asignar": [1,2,3],
      "desasignar": [4,5]
    }
    '''

    try:
        inc = Incidente.objects.get(pk=pk)
    except Incidente.DoesNotExist:
        return Response({"detail":"Incidente no encontrado"}, status=404)

    rescatista_id = request.data.get("rescatista")
    asignar = request.data.get("asignar") or []
    desasignar = request.data.get("desasignar") or []

    # ✅ set rescatista (opcional)
    if rescatista_id in [None, "", "null"]:
        inc.rescatista = None
        inc.save(update_fields=["rescatista"])
    else:
        try:
            inc.rescatista_id = int(rescatista_id)
            inc.save(update_fields=["rescatista"])
        except Exception:
            return Response({"error":"rescatista inválido"}, status=400)

    # estados de recurso (por nombre, fallback por id si ya lo tenías)
    estado_disponible = EstadoRecurso.objects.filter(nombre__iexact="Disponible").first()
    estado_asignado = EstadoRecurso.objects.filter(nombre__iexact="Asignado").first()

    # fallback si tus IDs están fijos
    if not estado_disponible:
        estado_disponible = EstadoRecurso.objects.filter(id=1).first()
    if not estado_asignado:
        estado_asignado = EstadoRecurso.objects.filter(id=2).first()

    # 1) Asignar nuevos recursos
    for rid in asignar:
        try:
            rid_int = int(rid)
        except Exception:
            continue

        if Asignacion.objects.filter(incidente=inc, recurso_id=rid_int, activo=True).exists():
            continue

        Asignacion.objects.create(incidente=inc, recurso_id=rid_int)

        if estado_asignado:
            Recurso.objects.filter(id=rid_int).update(estado=estado_asignado)

    # 2) Desasignar recursos
    for rid in desasignar:
        try:
            rid_int = int(rid)
        except Exception:
            continue

        # buscamos el último registro aunque esté soft-delete
        asig = Asignacion.all_objects.filter(
            incidente=inc,
            recurso_id=rid_int
        ).order_by("-id").first()

        if asig:
            asig.soft_delete()

        if estado_disponible:
            Recurso.objects.filter(
                id=rid_int
            ).update(estado=estado_disponible)


    # 🔔 Evento tiempo real (rescatista + admin + operador)
    channel_layer = get_channel_layer()
    for grupo in ["rol_rescatista", "rol_admin", "rol_operador"]:
        async_to_sync(channel_layer.group_send)(
            grupo,
            {
                "type":"enviar_evento",
                "data":{
                    "accion":"incidente_update"
                }
            }
        )


    return Response({"ok":"asignación actualizada"})


# ---------------- AUDITOR ----------------

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAuditor])
def historial_incidente(request, pk):

    qs = HistorialIncidente.objects.filter(incidente_id=pk)

    return Response({
        "mensaje": "Endpoint activo",
        "total": qs.count()
    })


# ---------------- DETALLES CATÁLOGOS ----------------
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


# ---------------- TIPO RECURSO ----------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def tipo_recurso_api(request):

    if request.method == "GET":
        qs = TipoRecurso.objects.all()
        return Response(TipoRecursoSerializer(qs, many=True).data)

    if request.method == "POST":
        ser = TipoRecursoSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=201)
        return Response(ser.errors, status=400)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def estado_recurso_api(request):

    if request.method == "GET":
        qs = EstadoRecurso.objects.all()
        return Response(EstadoRecursoSerializer(qs, many=True).data)

    if request.method == "POST":
        ser = EstadoRecursoSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=201)
        return Response(ser.errors, status=400)


@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def tipo_recurso_detalle(request, pk):

    try:
        obj = TipoRecurso.objects.get(pk=pk)
    except:
        return Response({"error":"No existe"}, status=404)

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

    if request.method == "DELETE":

        try:
            obj.delete()
            return Response(status=204)

        except ProtectedError:
            return Response({"error":"No se puede eliminar porque está en uso"}, status=409)


@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsAdmin])
def estado_recurso_detalle(request, pk):

    try:
        obj = EstadoRecurso.objects.get(pk=pk)
    except:
        return Response({"error":"No existe"}, status=404)

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

    if request.method == "DELETE":

        try:
            obj.delete()
            return Response(status=204)

        except ProtectedError:
            return Response({"error":"No se puede eliminar porque está en uso"}, status=409)


def liberar_recursos_incidente(inc):
    # estado disponible
    estado_disponible = EstadoRecurso.objects.filter(
        nombre__iexact="Disponible"
    ).first()

    if not estado_disponible:
        estado_disponible = EstadoRecurso.objects.filter(id=1).first()

    # buscar asignaciones activas
    asignaciones = Asignacion.objects.filter(
        incidente=inc,
        activo=True
    )

    for a in asignaciones:
        # soft delete asignación
        a.soft_delete()

        # liberar recurso
        if estado_disponible:
            Recurso.objects.filter(id=a.recurso_id).update(
                estado=estado_disponible
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrOperador])
def auditoria_incidente(request, pk):

    logs = AuditoriaAccion.objects.filter(
        registro_id=pk,
        tabla="incidente"
    ).order_by("fecha")

    data = []

    for a in logs:
        data.append({
            "usuario": a.usuario.username if a.usuario else "-",
            "rol": a.rol,
            "accion": a.accion,
            "metodo": a.metodo,
            "endpoint": a.endpoint,
            "fecha": a.fecha.strftime("%Y-%m-%d %H:%M:%S"),
            "data": a.data
        })

    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def incidentes_inactivos(request):

    qs = Incidente.all_objects.filter(is_deleted=True)

    data = IncidenteSerializer(qs, many=True).data
    return Response(data)



