from django.db import models

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .models import (
    Centro,
    Actividad,
    Bono,
    Profesor,
    BonoUsuario,
    HorarioSemanal,
    Reserva,
    Espacio,          
    ReservaEspacio,
    HorarioCentro    
)
from .serializers import CentroSerializer, ActividadSerializer
import json
from django.contrib.auth.decorators import login_required
User = get_user_model()
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import datetime, timedelta, date
from itertools import chain
from django.http import JsonResponse
from datetime import timedelta, datetime
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib.auth import logout

@api_view(['GET'])
def lista_centros(request):
    centros = Centro.objects.all()
    serializer = CentroSerializer(centros, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_lista_actividades(request):
    if not request.user.is_authenticated:
        return Response({"error": "No autenticado"}, status=401)

    actividades = Actividad.objects.filter(
        centro=request.user.centro
    )

    serializer = ActividadSerializer(actividades, many=True)
    return Response(serializer.data)


@csrf_exempt
def registro_usuario(request):
    if request.method == "POST":

        import json
        data = json.loads(request.body)

        try:
            if not data.get("centro"):
                return JsonResponse({"error": "Debes seleccionar un centro"}, status=400)

            try:
                centro = Centro.objects.get(id=data["centro"])
            except Centro.DoesNotExist:
                return JsonResponse({"error": "Centro no válido"}, status=400)

            if User.objects.filter(username=data["email"]).exists():
                return JsonResponse({"error": "Este correo ya está registrado"}, status=400)

            User.objects.create_user(
                username=data["email"],
                email=data["email"],
                password=data["password"],
                first_name=data.get("nombre"),
                last_name=data.get("apellidos"),
                fecha_nacimiento=data.get("fecha_nacimiento"),
                genero=data.get("genero"),
                centro=centro
            )

            return JsonResponse({"mensaje": "Usuario creado correctamente"})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def login_usuario(request):
    if request.method == "POST":
        data = json.loads(request.body)

        email = data.get("email")
        password = data.get("password")

        user = authenticate(username=email, password=password)

        if user is not None:
            django_login(request, user)

            if user.rol == "admin":
                redirect_url = "/panel-admin/"
            elif user.rol == "profesor":
                redirect_url = "/panel-profesor/"
            else:
                redirect_url = "/actividades/"

            return JsonResponse({
                "mensaje": "Login correcto",
                "redirect": redirect_url,
                "nombre": user.first_name,
                "apellido": user.last_name,
                "email": user.email
            })

        else:
            return JsonResponse({"error": "Credenciales incorrectas"}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
def perfil_usuario(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "No autenticado"}, status=401)

    if request.method == "GET":
        user = request.user

        return JsonResponse({
            "nombre": user.first_name,
            "apellido": user.last_name,
            "email": user.email,
            "fecha_nacimiento": user.fecha_nacimiento,
            "genero": user.genero
        })

    if request.method == "PUT":
        data = json.loads(request.body)
        user = request.user

        user.first_name = data.get("nombre")
        user.last_name = data.get("apellido")
        user.fecha_nacimiento = data.get("fecha_nacimiento")
        user.genero = data.get("genero")

        user.save()

        return JsonResponse({"mensaje": "Datos actualizados correctamente"})

    return JsonResponse({"error": "Método no permitido"}, status=405)

from django.shortcuts import render

def registro_view(request):
    return render(request, "registro.html")

def login_view(request):
    return render(request, "inicioSesion.html")

def actividades_view(request):
    return render(request, "actividades.html")

@login_required
def calendario_view(request):
    hoy = timezone.now().date()
    dia_actual = hoy.weekday()

    dia = request.GET.get("dia")

    if dia is not None:
        dia_activo = int(dia)
    else:
        dia_activo = dia_actual

    dias_base = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sab", "Dom"]

    dias_rotados = dias_base[dia_actual:] + dias_base[:dia_actual]
    indices_rotados = list(range(dia_actual, 7)) + list(range(0, dia_actual))

    dias_final = list(zip(indices_rotados, dias_rotados))

    ahora = timezone.now()

    reservas_clases = Reserva.objects.filter(
        usuario=request.user,
        activa=True,
        fecha_clase__gte=hoy
    ).select_related("horario", "horario__actividad")

    eventos_clases = []

    for r in reservas_clases:

        fecha_fin = datetime.combine(
            r.fecha_clase,
            r.horario.hora_fin
        )

        fecha_fin = timezone.make_aware(fecha_fin)

        if fecha_fin > ahora:
            if r.fecha_clase.weekday() == dia_activo:  
                eventos_clases.append({
                    "nombre": r.horario.actividad.nombre.upper(),
                    "hora_inicio": r.horario.hora_inicio,
                    "hora_fin": r.horario.hora_fin,
                    "color": r.horario.actividad.color
                })

    reservas_libres = ReservaEspacio.objects.filter(
        usuario=request.user,
        fecha__gte=hoy
    )

    eventos_libres = []

    for r in reservas_libres:

        fecha_fin = datetime.combine(r.fecha, r.hora_fin)
        fecha_fin = timezone.make_aware(fecha_fin)

        if fecha_fin > ahora:   
            if r.fecha.weekday() == dia_activo:
                eventos_libres.append({
                    "nombre": r.espacio.actividad.nombre.upper(),
                    "hora_inicio": r.hora_inicio,
                    "hora_fin": r.hora_fin,
                    "color": r.espacio.actividad.color
                })

    eventos = list(chain(eventos_clases, eventos_libres))

    eventos.sort(key=lambda x: x["hora_inicio"])

    return render(request, "calendario.html", {
        "eventos": eventos,
        "dia_activo": dia_activo,
        "dias": dias_final
    })


@login_required
def reservas_view(request):

    ahora = timezone.localtime()
    hoy = ahora.date()

    reservas = Reserva.objects.filter(
        usuario=request.user,
        activa=True
    ).select_related("horario", "horario__actividad")

    reservas_futuras = []

    for r in reservas:
        fecha_fin = datetime.combine(
            r.fecha_clase,
            r.horario.hora_fin
        )
        fecha_fin = timezone.make_aware(fecha_fin)
        fecha_fin = timezone.localtime(fecha_fin)

        if fecha_fin > ahora:
            reservas_futuras.append(r)

    reservas_espacios = ReservaEspacio.objects.filter(
        usuario=request.user,
        fecha__gte=hoy
    ).select_related("espacio", "espacio__actividad")

    reservas_espacios_futuras = []

    for r in reservas_espacios:
        fecha_fin = datetime.combine(
            r.fecha,
            r.hora_fin
        )
        fecha_fin = timezone.make_aware(fecha_fin)
        fecha_fin = timezone.localtime(fecha_fin)

        if fecha_fin > ahora:
            reservas_espacios_futuras.append(r)

    return render(request, "reservas.html", {
        "reservas_clases": reservas_futuras,
        "reservas_espacios": reservas_espacios_futuras
    })

def cuenta_view(request):
    return render(request, "cuenta.html")

def datos_view(request):
    return render(request, "datos.html")

def compras_view(request):
    return render(request, "compras.html")

def saldo_view(request):
    return render(request, "saldo.html")

def exterior_view(request):
    return render(request, "exterior.html")

def interior_view(request):
    return render(request, "interior.html")

def lista_actividades_view(request):
    return render(request, "lista-actividades.html")

def actividad_libre_view(request):
    return render(request, "actividad-libre.html")

def actividad_bono_view(request):
    return render(request, "actividad-bono.html")

def index_view(request):
    return render(request, "index.html")

def actividad_view(request):
    return render(request, "actividad.html")

@csrf_exempt
def comprar_bono(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "No autenticado"}, status=401)

    if request.method == "POST":
        data = json.loads(request.body)
        bono_id = data.get("bono_id")

        try:
            bono = Bono.objects.get(id=bono_id)

            bono_actual = BonoUsuario.objects.filter(
                usuario=request.user,
                activo=True
            ).order_by("-id").first()

            if bono_actual and bono_actual.clases_restantes > 0:
                return JsonResponse({
                    "error": "Debes gastar tus clases antes de comprar otro bono"
                }, status=400)

            BonoUsuario.objects.filter(
                usuario=request.user,
                activo=True
            ).update(activo=False)

            fecha_caducidad = timezone.now().date() + timedelta(days=30)

            BonoUsuario.objects.create(
                usuario=request.user,
                bono=bono,
                clases_restantes=bono.clases_totales,
                fecha_caducidad=fecha_caducidad,
                activo=True
            )

            return JsonResponse({"mensaje": "Bono comprado correctamente"})

        except Bono.DoesNotExist:
            return JsonResponse({"error": "Bono no encontrado"}, status=404)

    return JsonResponse({"error": "Método no permitido"}, status=405)

from django.utils import timezone
from datetime import datetime

def mi_bono(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "No autenticado"}, status=401)

    bono_usuario = BonoUsuario.objects.filter(
        usuario=request.user,
        activo=True
    ).order_by("-id").first()

    if not bono_usuario:
        return JsonResponse({"mensaje": "No tiene bono activo"})

    ahora = timezone.localtime()

    reservas = Reserva.objects.filter(
        bono_usuario=bono_usuario,
        activa=True
    )
    gastadas = 0
    en_uso = 0

    for r in reservas:
        fecha_fin = datetime.combine(
            r.fecha_clase,
            r.horario.hora_fin
        )

        fecha_fin = timezone.make_aware(fecha_fin)
        fecha_fin = timezone.localtime(fecha_fin)

        if fecha_fin <= ahora:
            gastadas += 1
        else:
            en_uso += 1

    return JsonResponse({
        "nombre": bono_usuario.bono.nombre,
        "clases_restantes": bono_usuario.clases_restantes,
        "clases_totales": bono_usuario.bono.clases_totales,
        "fecha_caducidad": bono_usuario.fecha_caducidad,
        "en_uso": en_uso,
        "gastadas": gastadas
    })


def logout_usuario(request):

    logout(request)

    return redirect("login")

@csrf_exempt
def reservar_clase(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "No autenticado"}, status=401)

    if request.method == "POST":
        data = json.loads(request.body)

        horario_id = data.get("horario_id")
        fecha = data.get("fecha")  

        if not fecha:
            return JsonResponse({"error": "Fecha no válida"}, status=400)

        try:
            horario = HorarioSemanal.objects.get(id=horario_id)

            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()

            hoy = timezone.now().date()
            limite = hoy + timedelta(days=7)

            if fecha_obj < hoy or fecha_obj > limite:
                return JsonResponse(
                    {"error": "Solo puedes reservar hasta dentro de 7 días"},
                    status=400
                )

            fecha_hora_inicio = datetime.combine(
                fecha_obj,
                horario.hora_inicio
            )

            fecha_hora_inicio = timezone.make_aware(fecha_hora_inicio)

            if fecha_hora_inicio <= timezone.now():
                return JsonResponse(
                    {"error": "No puedes reservar una clase que ya ha comenzado"},
                    status=400
                )
            plazas_ocupadas = Reserva.objects.filter(
                horario=horario,
                fecha_clase=fecha_obj,
                activa=True
            ).count()

            if plazas_ocupadas >= horario.plazas_totales:
                return JsonResponse({"error": "Clase completa"}, status=400)

            bono_usuario = BonoUsuario.objects.filter(
                usuario=request.user,
                activo=True
            ).order_by("-id").first()

            if not bono_usuario or bono_usuario.clases_restantes <= 0:
                return JsonResponse({"error": "Sin clases disponibles"}, status=400)

            if Reserva.objects.filter(
                usuario=request.user,
                horario=horario,
                fecha_clase=fecha_obj,
                activa=True
            ).exists():
                return JsonResponse(
                    {"error": "Ya tienes esta clase reservada"},
                    status=400
                )

            Reserva.objects.create(
                usuario=request.user,
                horario=horario,
                fecha_clase=fecha_obj,
                bono_usuario=bono_usuario
            )

            bono_usuario.clases_restantes -= 1
            bono_usuario.save()

            return JsonResponse({"mensaje": "Reserva realizada correctamente"})

        except HorarioSemanal.DoesNotExist:
            return JsonResponse({"error": "Horario no encontrado"}, status=404)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
def cancelar_reserva(request, reserva_id):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "No autenticado"}, status=401)

    try:
        reserva = Reserva.objects.get(
            id=reserva_id,
            usuario=request.user,
            activa=True
        )
    except Reserva.DoesNotExist:
        return JsonResponse({"error": "Reserva no encontrada"}, status=404)

    fecha = reserva.fecha_clase
    hora = reserva.horario.hora_inicio

    fecha_hora_clase = datetime.combine(fecha, hora)
    fecha_hora_clase = timezone.make_aware(fecha_hora_clase)

    ahora = timezone.now()

    if fecha_hora_clase <= ahora + timedelta(minutes=30):
        return JsonResponse(
            {"error": "No puedes cancelar con menos de 30 minutos de antelación"},
            status=400
        )

    reserva.activa = False
    reserva.save()

    bono_usuario = BonoUsuario.objects.filter(
        usuario=request.user,
        activo=True
    ).first()

    if bono_usuario:
        bono_usuario.clases_restantes += 1
        bono_usuario.save()

    return JsonResponse({"success": "Reserva cancelada correctamente"})
@csrf_exempt
def cancelar_reserva_espacio(request, reserva_id):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "No autenticado"}, status=401)

    try:
        reserva = ReservaEspacio.objects.get(
            id=reserva_id,
            usuario=request.user
        )
    except ReservaEspacio.DoesNotExist:
        return JsonResponse({"error": "Reserva no encontrada"}, status=404)

    fecha_hora_reserva = datetime.combine(
        reserva.fecha,
        reserva.hora_inicio
    )
    fecha_hora_reserva = timezone.make_aware(fecha_hora_reserva)

    ahora = timezone.now()

    if fecha_hora_reserva <= ahora + timedelta(minutes=30):
        return JsonResponse(
            {"error": "No puedes cancelar con menos de 30 minutos de antelación"},
            status=400
        )

    reserva.delete()   
    return JsonResponse({"success": "Reserva cancelada correctamente"})
        
def lista_bonos(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "No autenticado"}, status=401)

    bonos = Bono.objects.filter(centro=request.user.centro)

    data = []
    for bono in bonos:
        data.append({
            "id": bono.id,
            "nombre": bono.nombre,
            "clases_totales": bono.clases_totales,
            "precio": str(bono.precio)
        })

    return JsonResponse(data, safe=False)

@api_view(['GET'])

def api_actividad_detalle(request, id):

    if not request.user.is_authenticated:
        return Response({"error": "No autenticado"}, status=401)

    try:
        actividad = Actividad.objects.get(id=id, centro=request.user.centro)

        if actividad.tipo == "libre":

            espacios = Espacio.objects.filter(actividad=actividad)

            data = {
                "id": actividad.id,
                "nombre": actividad.nombre,
                "tipo": "libre",
                "precio": actividad.precio,
                "espacios": [
                    {
                        "id": e.id,
                        "nombre": e.nombre
                    } for e in espacios
                ]
            }

            return Response(data)

        if actividad.tipo == "bono":

            hoy = timezone.now().date()
            limite = hoy + timedelta(days=7)

            horarios = HorarioSemanal.objects.filter(
                actividad=actividad
            )

            clases_generadas = []

            for i in range(0, 8):
                fecha = hoy + timedelta(days=i)
                dia_semana = fecha.weekday()

                horarios_dia = horarios.filter(dia_semana=dia_semana)

                for h in horarios_dia:

                    plazas_ocupadas = Reserva.objects.filter(
                        horario=h,
                        fecha_clase=fecha,   
                        activa=True
                    ).count()

                    clases_generadas.append({
                        "id": h.id,
                        "fecha": fecha,
                        "hora_inicio": h.hora_inicio.strftime("%H:%M"),
                        "hora_fin": h.hora_fin.strftime("%H:%M"),
                        "monitor": h.profesor.nombre if h.profesor else "",
                        "plazas_maximas": h.plazas_totales,
                        "plazas_ocupadas": plazas_ocupadas
                    })

            return Response({
                "id": actividad.id,
                "nombre": actividad.nombre,
                "tipo": "bono",
                "clases": clases_generadas
            })

    except Actividad.DoesNotExist:
        return Response({"error": "No encontrada"}, status=404)
    
@csrf_exempt
def reservar_espacio(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "No autenticado"}, status=401)

    if request.method == "POST":
        data = json.loads(request.body)

        espacio_id = data.get("espacio_id")
        fecha = data.get("fecha")

        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()

        if fecha_obj < date.today():
            return JsonResponse(
                {"error": "No puedes reservar días anteriores"},
                status=400
            )

        hora_inicio = data.get("hora_inicio")
        duracion = float(data.get("duracion"))

        hora_inicio_dt = datetime.strptime(hora_inicio, "%H:%M")
        hora_fin_dt = hora_inicio_dt + timedelta(hours=duracion)
        hora_fin = hora_fin_dt.time()

        fecha_hora_inicio = datetime.combine(fecha_obj, hora_inicio_dt.time())
        fecha_hora_inicio = timezone.make_aware(fecha_hora_inicio)

        ahora = timezone.now()

        if fecha_hora_inicio <= ahora:
            return JsonResponse(
                {"error": "No puedes reservar en una hora pasada"},
                status=400
            )

        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
        dia_semana = fecha_dt.weekday()

        espacio = Espacio.objects.get(id=espacio_id)
        centro = espacio.actividad.centro

        bloques = HorarioCentro.objects.filter(
            centro=centro,
            dia_semana=dia_semana
        )

        if not bloques.exists():
            return JsonResponse({"error": "El centro está cerrado ese día"}, status=400)

        valido = False

        for bloque in bloques:
            if (
                hora_inicio_dt.time() >= bloque.hora_inicio
                and hora_fin <= bloque.hora_fin
            ):
                valido = True
                break

        if not valido:
            return JsonResponse({"error": "Fuera del horario permitido"}, status=400)

        conflicto = ReservaEspacio.objects.filter(
            espacio_id=espacio_id,
            fecha=fecha,
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio
        ).exists()

        if conflicto:
            return JsonResponse({"error": "Ese horario ya está reservado"}, status=400)

        ReservaEspacio.objects.create(
            usuario=request.user,
            espacio_id=espacio_id,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        )

        return JsonResponse({"mensaje": "Reserva realizada correctamente"})

    return JsonResponse({"error": "Método no permitido"}, status=405)

@login_required
def panel_centro_view(request):

    if request.user.rol != "profesor":
        return redirect("actividades")

    centro = request.user.centro

    actividades = Actividad.objects.filter(
        centro=centro,
        tipo="bono"
    )

    return render(request, "panel-profesor/dashboard.html", {
        "actividades": actividades
    })

@login_required
def panel_actividad_view(request, actividad_id):

    if request.user.rol != "profesor":
        return redirect("actividades")

    actividad = Actividad.objects.get(
        id=actividad_id,
        centro=request.user.centro
    )

    horarios = HorarioSemanal.objects.filter(
        actividad=actividad
    ).select_related("profesor")

    ahora = timezone.localtime()
    hoy = ahora.date()
    hora_actual = ahora.time()

    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    clases = []

    for h in horarios:

        reservas = Reserva.objects.filter(
            horario=h,
            activa=True,
            estado="reservada",
            fecha_clase__gte=hoy,
            fecha_clase__week_day=h.dia_semana + 2
        ).select_related("usuario")

        reservas_validas = []

        for r in reservas:
            if r.fecha_clase > hoy:
                reservas_validas.append(r)
            elif r.fecha_clase == hoy and h.hora_fin > hora_actual:
                reservas_validas.append(r)

        clases.append({
            "dia": h.dia_semana,
            "hora_inicio": h.hora_inicio,
            "hora_fin": h.hora_fin,
            "profesor": h.profesor.nombre if h.profesor else "Sin profesor",
            "plazas_totales": h.plazas_totales,
            "plazas_ocupadas": len(reservas_validas),
            "alumnos": reservas_validas
        })

    dias = [
        (0, "Lun"),
        (1, "Mar"),
        (2, "Mié"),
        (3, "Jue"),
        (4, "Vie"),
        (5, "Sáb"),
        (6, "Dom"),
    ]

    return render(request, "panel-profesor/actividad.html", {
        "actividad": actividad,
        "clases": clases,
        "dias": dias
    })

@login_required
def panel_calendario_view(request):

    if request.user.rol != "profesor":
        return redirect("actividades")

    centro = request.user.centro

    horarios = HorarioSemanal.objects.filter(
        actividad__centro=centro
    ).select_related("actividad")

    dias = [
        {"numero": 0, "nombre": "Lun", "clases": []},
        {"numero": 1, "nombre": "Mar", "clases": []},
        {"numero": 2, "nombre": "Mié", "clases": []},
        {"numero": 3, "nombre": "Jue", "clases": []},
        {"numero": 4, "nombre": "Vie", "clases": []},
        {"numero": 5, "nombre": "Sáb", "clases": []},
        {"numero": 6, "nombre": "Dom", "clases": []},
    ]

    for h in horarios:
        dias[h.dia_semana]["clases"].append({
            "actividad": h.actividad.nombre,
            "hora_inicio": h.hora_inicio.strftime("%H:%M"),
            "hora_fin": h.hora_fin.strftime("%H:%M"),
            "color": h.actividad.color
        })

    return render(request, "panel-profesor/calendario.html", {
        "dias": dias
    })

from datetime import date, timedelta

@login_required
def panel_espacios_view(request):

    if request.user.rol != "profesor":
        return redirect("actividades")

    centro = request.user.centro

    ahora = timezone.localtime()
    hoy = ahora.date()
    hora_actual = ahora.time()

    dias = []
    dias_es = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    for i in range(7):
        fecha = hoy + timedelta(days=i)

        reservas = ReservaEspacio.objects.filter(
            espacio__actividad__centro=centro,
            fecha=fecha
        ).select_related("usuario", "espacio")

        reservas_validas = []

        for r in reservas:
            if r.fecha > hoy:
                reservas_validas.append(r)
            elif r.fecha == hoy and r.hora_fin > hora_actual:
                reservas_validas.append(r)

        dias.append({
            "fecha": fecha,
            "nombre": dias_es[fecha.weekday()], 
            "reservas": sorted(reservas_validas, key=lambda x: x.hora_inicio)
        })

    return render(request, "panel-profesor/espacios.html", {
        "dias": dias
    })


@login_required
def panel_admin_view(request):

    if request.user.rol != "admin":
        return redirect("actividades")

    return redirect("admin_actividades")

@login_required
def admin_actividades_view(request):

    if request.user.rol != "admin":
        return redirect("actividades")

    actividades = Actividad.objects.filter(
        centro=request.user.centro
    )

    return render(request, "panel-admin/actividades.html", {
        "actividades": actividades
    })

from django.views.decorators.http import require_POST

@login_required
@require_POST
def admin_crear_actividad(request):

    if request.user.rol != "admin":
        return JsonResponse({"error": "No autorizado"}, status=403)

    nombre = request.POST.get("nombre")
    tipo = request.POST.get("tipo")
    categoria = request.POST.get("categoria")
    precio = request.POST.get("precio")
    color = request.POST.get("color")
    imagen = request.FILES.get("imagen")

    if not nombre or not tipo:
        return JsonResponse({"error": "Datos incompletos"}, status=400)

    if tipo == "libre":
        if not precio:
            return JsonResponse({"error": "Las actividades libres necesitan precio"}, status=400)
    else:
        precio = None

    actividad = Actividad.objects.create(
        nombre=nombre,
        tipo=tipo,
        categoria=categoria,
        precio=precio if tipo == "libre" else None,
        color=color or "#1565c0",
        imagen=imagen,
        centro=request.user.centro
    )

    return JsonResponse({
        "success": True
    })
@login_required
def admin_horarios_actividad(request, actividad_id):

    if request.user.rol != "admin":
        return redirect("actividades")

    actividad = Actividad.objects.get(
        id=actividad_id,
        centro=request.user.centro
    )

    horarios = HorarioSemanal.objects.filter(
        actividad=actividad
    ).order_by("dia_semana", "hora_inicio")


    profesores = Profesor.objects.filter(
        centro=request.user.centro
    )

    return render(request, "panel-admin/horarios.html", {
        "actividad": actividad,
        "horarios": horarios,
        "profesores": profesores  
    })

@login_required
@require_POST
def admin_crear_horario(request):

    if request.user.rol != "admin":
        return JsonResponse({"error": "No autorizado"}, status=403)

    actividad_id = request.POST.get("actividad_id")
    dia_semana = request.POST.get("dia_semana")
    hora_inicio = request.POST.get("hora_inicio")
    hora_fin = request.POST.get("hora_fin")
    plazas = request.POST.get("plazas_totales")
    profesor_id = request.POST.get("profesor") 

    if not profesor_id:
        return JsonResponse({"error": "Debes seleccionar un profesor"}, status=400)

    actividad = Actividad.objects.get(
        id=actividad_id,
        centro=request.user.centro
    )

    try:
        profesor = Profesor.objects.get(
            id=profesor_id,
            centro=request.user.centro
        )
    except Profesor.DoesNotExist:
        return JsonResponse({"error": "Profesor no válido"}, status=400)

    HorarioSemanal.objects.create(
        actividad=actividad,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        plazas_totales=plazas,
        profesor=profesor 
    )

    return JsonResponse({"success": True})


@login_required
def admin_eliminar_actividad(request, actividad_id):

    if request.user.rol != "admin":
        return JsonResponse({"error": "No autorizado"}, status=403)

    actividad = Actividad.objects.get(
        id=actividad_id,
        centro=request.user.centro
    )

    actividad.delete()

    return JsonResponse({"success": True})

@login_required
def admin_eliminar_horario(request, horario_id):

    if request.user.rol != "admin":
        return JsonResponse({"error": "No autorizado"}, status=403)

    horario = HorarioSemanal.objects.get(id=horario_id)

    horario.delete()

    return JsonResponse({"success": True})

@login_required
def admin_profesores(request):

    if request.user.rol != "admin":
        return redirect("actividades")

    profesores = Profesor.objects.filter(
        centro=request.user.centro
    )

    return render(request, "panel-admin/profesores.html", {
        "profesores": profesores
    })

@login_required
@require_POST
def admin_crear_profesor(request):

    nombre = request.POST.get("nombre")

    Profesor.objects.create(
        nombre=nombre,
        centro=request.user.centro
    )

    return JsonResponse({"success": True})

@login_required
def admin_eliminar_profesor(request, profesor_id):

    profesor = Profesor.objects.get(
        id=profesor_id,
        centro=request.user.centro
    )

    profesor.delete()

    return JsonResponse({"success": True})

@login_required
def admin_espacios_actividad(request, actividad_id):

    actividad = Actividad.objects.get(
        id=actividad_id,
        centro=request.user.centro
    )

    espacios = Espacio.objects.filter(
        actividad=actividad
    )

    return render(request, "panel-admin/espacios_actividad.html", {
        "actividad": actividad,
        "espacios": espacios
    })

@login_required
@require_POST
def admin_crear_espacio(request):

    actividad_id = request.POST.get("actividad_id")
    nombre = request.POST.get("nombre")

    actividad = Actividad.objects.get(
        id=actividad_id,
        centro=request.user.centro
    )

    Espacio.objects.create(
        nombre=nombre,
        actividad=actividad
    )

    return JsonResponse({"success": True})

@login_required
def admin_eliminar_espacio(request, espacio_id):

    espacio = Espacio.objects.get(
        id=espacio_id,
        actividad__centro=request.user.centro
    )

    espacio.delete()

    return JsonResponse({"success": True})


@login_required
def admin_horarios_centro(request):

    if request.user.rol != "admin":
        return redirect("actividades")

    horarios = HorarioCentro.objects.filter(
        centro=request.user.centro
    ).order_by("dia_semana", "hora_inicio")

    return render(request, "panel-admin/horarios_centro.html", {
        "horarios": horarios
    })

@login_required
@require_POST
def admin_crear_horario_centro(request):

    dia_semana = request.POST.get("dia_semana")
    hora_inicio = request.POST.get("hora_inicio")
    hora_fin = request.POST.get("hora_fin")

    HorarioCentro.objects.create(
        centro=request.user.centro,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin
    )

    return JsonResponse({"success": True})

@login_required
def admin_eliminar_horario_centro(request, horario_id):

    horario = HorarioCentro.objects.get(
        id=horario_id,
        centro=request.user.centro
    )

    horario.delete()

    return JsonResponse({"success": True})

@login_required
def admin_bonos(request):

    if request.user.rol != "admin":
        return redirect("actividades")

    bonos = Bono.objects.filter(
        centro=request.user.centro
    )

    return render(request, "panel-admin/bonos.html", {
        "bonos": bonos
    })

@login_required
@require_POST
def admin_crear_bono(request):

    nombre = request.POST.get("nombre")
    clases = request.POST.get("clases")
    precio = request.POST.get("precio")

    Bono.objects.create(
        nombre=nombre,
        clases_totales=clases,
        precio=precio,
        centro=request.user.centro
    )

    return JsonResponse({"success": True})

@login_required
def admin_eliminar_bono(request, bono_id):

    bono = Bono.objects.get(
        id=bono_id,
        centro=request.user.centro
    )

    bono.delete()

    return JsonResponse({"success": True})


import requests
import os
from django.http import JsonResponse
import json

@csrf_exempt
def chatbot(request):
    return JsonResponse({"respuesta": "Funciona"})
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            mensaje = body.get("mensaje", "")

            headers = {
                "Authorization": f"Bearer {os.getenv('HF_TOKEN')}"
            }

            response = requests.post(
                "https://api-inference.huggingface.co/models/google/flan-t5-small",
                headers=headers,
                json={
                    "inputs": f"""
                Eres un asistente de una app de gimnasio llamada Hubit.
                Responde de forma breve, clara y útil.

                Usuario: {mensaje}
                Respuesta:
                """
                },
                timeout=10
            )

            data = response.json()
            print("HF RESPONSE:", data)

            # 🔴 ERROR (modelo cargando o fallo)
            if isinstance(data, dict) and "error" in data:
                return JsonResponse({
                    "respuesta": "Estoy despertando... prueba en unos segundos 😅"
                })

            # 🟢 RESPUESTA OK
            if isinstance(data, list):
                respuesta = data[0].get("generated_text", "")
            else:
                respuesta = "No tengo respuesta"

            return JsonResponse({"respuesta": respuesta})

        except requests.exceptions.Timeout:
            return JsonResponse({"respuesta": "Estoy tardando demasiado 😅"})

        except Exception as e:
            print("ERROR:", e)
            return JsonResponse({"respuesta": "Error del servidor"})

    return JsonResponse({"respuesta": "Método no permitido"})