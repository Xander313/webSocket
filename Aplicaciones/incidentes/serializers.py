from rest_framework import serializers
import magic
from .models import *

class TipoIncidenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoIncidente
        fields = "__all__"


class SeveridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Severidad
        fields = "__all__"


class EstadoIncidenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoIncidente
        fields = "__all__"


class IncidenteSerializer(serializers.ModelSerializer):
    
    creado_por = serializers.ReadOnlyField(source="creado_por.username")
    tipo_nombre = serializers.CharField(source="tipo.nombre", read_only=True)
    severidad_nombre = serializers.CharField(source="severidad.nombre", read_only=True)
    estado_nombre = serializers.CharField(source="estado.nombre", read_only=True)

    class Meta:
        model = Incidente
        fields = "__all__"
    def create(self, validated_data):
        validated_data["activo"] = True
        return super().create(validated_data)
    
    def validate_evidencia(self, file):

        if not file:
            return file

        mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)

        mime_validos = [
            "image/jpeg",
            "image/png",
            "application/pdf"
        ]

        if mime not in mime_validos:
            raise serializers.ValidationError(
                "Tipo de archivo inválido (solo JPG, PNG, PDF)"
            )

        return file

class RecursoSerializer(serializers.ModelSerializer):

    tipo_nombre = serializers.CharField(
        source="tipo.nombre",
        read_only=True
    )

    estado_nombre = serializers.CharField(
        source="estado.nombre",
        read_only=True
    )

    class Meta:
        model = Recurso
        fields = "__all__"



class AsignacionSerializer(serializers.ModelSerializer):

    recurso_nombre = serializers.CharField(
        source="recurso.nombre",
        read_only=True
    )

    incidente_id = serializers.ReadOnlyField(
        source="incidente.id"
    )

    class Meta:
        model = Asignacion
        fields = "__all__"




class TipoRecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoRecurso
        fields = "__all__"


class EstadoRecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoRecurso
        fields = "__all__"
