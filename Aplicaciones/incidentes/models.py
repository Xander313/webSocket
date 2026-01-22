from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# =======================
# BASE SOFT DELETE
# =======================

class SoftDeleteModel(models.Model):
    activo = models.BooleanField(default=True)
    fecha_borrado = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.activo = False
        self.fecha_borrado = timezone.now()
        self.save()

    def restore(self):
        self.activo = True
        self.fecha_borrado = None
        self.save()


class ActivosManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(activo=True)


# =======================
# CATÁLOGOS
# =======================

class TipoIncidente(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Severidad(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    nivel = models.IntegerField()

    def __str__(self):
        return self.nombre


class EstadoIncidente(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


class TipoRecurso(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class EstadoRecurso(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


# =======================
# ENTIDADES
# =======================

class Incidente(SoftDeleteModel):

    tipo = models.ForeignKey(TipoIncidente, on_delete=models.PROTECT)
    severidad = models.ForeignKey(Severidad, on_delete=models.PROTECT)
    estado = models.ForeignKey(EstadoIncidente, on_delete=models.PROTECT)

    descripcion = models.TextField()
    latitud = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, default=0)

    evidencia = models.FileField(upload_to="incidentes/", null=True, blank=True)

    creado_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="incidentes_creados"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    objects = ActivosManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"Incidente #{self.id}"


class Recurso(SoftDeleteModel):

    nombre = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoRecurso, on_delete=models.PROTECT)
    estado = models.ForeignKey(EstadoRecurso, on_delete=models.PROTECT)
    capacidad = models.TextField()

    objects = ActivosManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.nombre


class Asignacion(SoftDeleteModel):

    incidente = models.ForeignKey(Incidente, on_delete=models.CASCADE)
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE)

    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    objects = ActivosManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.recurso} → Incidente {self.incidente.id}"


# =======================
# HISTORIAL
# =======================

class HistorialIncidente(models.Model):
    incidente = models.ForeignKey(Incidente, on_delete=models.CASCADE)
    estado = models.ForeignKey(EstadoIncidente, on_delete=models.PROTECT)

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True)

    def __str__(self):
        return f"Incidente {self.incidente.id} - {self.estado.nombre}"


# =======================
# AUDITORÍA
# =======================

class AuditoriaAccion(models.Model):

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    rol = models.CharField(max_length=50)
    accion = models.CharField(max_length=50)
    metodo = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=255)

    tabla = models.CharField(max_length=50)
    registro_id = models.IntegerField(null=True, blank=True)

    ip = models.GenericIPAddressField()
    user_agent = models.TextField()
    data = models.JSONField(null=True, blank=True)

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.usuario} - {self.accion}"
