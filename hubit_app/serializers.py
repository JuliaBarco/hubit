from rest_framework import serializers
from .models import Centro, Actividad

class CentroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Centro
        fields = '__all__'

class ActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actividad
        fields = '__all__'