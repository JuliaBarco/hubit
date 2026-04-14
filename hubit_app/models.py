from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractUser


class Centro(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=300)
    
    def __str__(self):
        return self.nombre
    
class Usuario(AbstractUser):

    ROL_CHOICES = [
        ('cliente', 'Cliente'),
        ('profesor', 'Profesor'),
        ('admin', 'Administrador Centro'),
    ]

    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default='cliente'
    )

    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=10, null=True, blank=True)
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.username

class Profesor(models.Model):
    nombre = models.CharField(max_length=150)
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

class Actividad(models.Model):

    TIPO_CHOICES = [
        ('libre', 'Actividad libre'),
        ('bono', 'Actividad con bono'),
    ]

    CATEGORIA_CHOICES = [
        ('interior', 'Interior'),
        ('exterior', 'Exterior'),
    ]

    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        default="interior"
    )
    imagen = models.ImageField(upload_to='actividades/', null=True, blank=True)
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    color = models.CharField(
        max_length=7,
        default="#1e88e5"
    )

    def save(self, *args, **kwargs):
        if not self.color.startswith("#"):
            self.color = f"#{self.color}"
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.tipo == "libre" and self.precio is None:
            raise ValidationError("Las actividades libres deben tener precio.")

        if self.tipo == "bono":
            self.precio = None

    def __str__(self):
        return self.nombre

class HorarioSemanal(models.Model):

    DIAS = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    dia_semana = models.IntegerField(choices=DIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    profesor = models.ForeignKey(Profesor, on_delete=models.SET_NULL, null=True)
    plazas_totales = models.IntegerField()

    def __str__(self):
        return f"{self.actividad.nombre} - {self.get_dia_semana_display()} {self.hora_inicio}"
    
class Bono(models.Model):
    nombre = models.CharField(max_length=100)
    clases_totales = models.IntegerField()
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

class BonoUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    bono = models.ForeignKey(Bono, on_delete=models.CASCADE)

    clases_restantes = models.IntegerField()
    fecha_compra = models.DateField(auto_now_add=True)
    fecha_caducidad = models.DateField()

    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.bono.nombre}"


class Reserva(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    horario = models.ForeignKey(HorarioSemanal, on_delete=models.CASCADE)
    bono_usuario = models.ForeignKey(
        BonoUsuario,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    fecha_clase = models.DateField()  

    fecha_reserva = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    estado = models.CharField(
        max_length=10,
        choices=[
            ("reservada", "Reservada"),
            ("gastada", "Gastada"),
        ],
        default="reservada"
    )

    def __str__(self):
        return f"{self.usuario.username} - {self.horario} - {self.fecha_clase}"
    
class Espacio(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)  

    def __str__(self):
        return f"{self.nombre} - {self.actividad.nombre}"

class ReservaEspacio(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.usuario} - {self.espacio}"
    
class HorarioCentro(models.Model):

    DIAS = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    centro = models.ForeignKey(Centro, on_delete=models.CASCADE, related_name="horarios")

    dia_semana = models.IntegerField(choices=DIAS)

    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.centro.nombre} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"