from django.contrib import admin
from django import forms
from .models import (
    Usuario,
    Centro,
    Profesor,
    Actividad,
    HorarioSemanal,
    Bono,
    BonoUsuario,
    Reserva,
    Espacio,
    ReservaEspacio,
    HorarioCentro
)

# ==========================
# REGISTROS SIMPLES
# ==========================


admin.site.register(Centro)
admin.site.register(Profesor)
admin.site.register(HorarioSemanal)
admin.site.register(Bono)
admin.site.register(BonoUsuario)
admin.site.register(Reserva)
admin.site.register(Espacio)
admin.site.register(ReservaEspacio)


# ==========================
# HORARIO CENTRO
# ==========================

@admin.register(HorarioCentro)
class HorarioCentroAdmin(admin.ModelAdmin):
    list_display = ("centro", "dia_semana", "hora_inicio", "hora_fin")


# ==========================
# FORM PERSONALIZADO PARA COLOR PICKER
# ==========================

class ActividadForm(forms.ModelForm):
    color = forms.CharField(
        widget=forms.TextInput(attrs={"type": "color"})
    )

    class Meta:
        model = Actividad
        fields = "__all__"


# ==========================
# ACTIVIDAD ADMIN
# ==========================

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    form = ActividadForm

    def get_fields(self, request, obj=None):
        fields = ["nombre", "tipo", "categoria", "imagen", "centro", "color"]

        if obj and obj.tipo == "libre":
            fields.append("precio")

        if obj is None:
            fields.append("precio")

        return fields
    
from django.contrib.auth.admin import UserAdmin

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        ("Información extra", {
            "fields": ("rol", "centro", "fecha_nacimiento", "genero")
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Información extra", {
            "fields": ("rol", "centro", "fecha_nacimiento", "genero")
        }),
    )

    list_display = ("username", "email", "rol", "centro", "is_staff")