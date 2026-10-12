import os

from models import Estudiante, Materia, Matricula
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido


# La ruta parte de esta carpeta, aunque se ejecute main.py desde otro lugar.
CARPETA_DATOS = os.path.join(os.path.dirname(__file__), "data")
gestor_estudiantes = GestorJSON(os.path.join(CARPETA_DATOS, "estudiantes.json"))
gestor_materias = GestorJSON(os.path.join(CARPETA_DATOS, "materias.json"))
gestor_matriculas = GestorJSON(os.path.join(CARPETA_DATOS, "matriculas.json"))


# =====================================================================
# FUNCIONES GENÉRICAS: sirven para los tres modelos
# =====================================================================
def leer_objetos(gestor, clase):
    objetos = []
    for datos in gestor.leer():
        objetos.append(clase.desde_diccionario(datos))
    return objetos


def obtener_por_id(gestor, clase, id_registro):
    for objeto in leer_objetos(gestor, clase):
        if objeto.id == id_registro:
            return objeto
    return None


def buscar(gestor, clase, termino, campos):
    termino = termino.strip().lower()
    encontrados = []
    if termino == "":
        return encontrados

    for objeto in leer_objetos(gestor, clase):
        for campo in campos:
            if termino in str(getattr(objeto, campo)).lower():
                encontrados.append(objeto)
                break
    return encontrados


def siguiente_id(gestor):
    mayor = 0
    for datos in gestor.leer():
        if datos["id"] > mayor:
            mayor = datos["id"]
    return mayor + 1


def guardar_nuevo(gestor, objeto):
    datos = gestor.leer()
    datos.append(objeto.a_diccionario())
    return gestor.guardar(datos)


def reemplazar(gestor, objeto):
    datos = gestor.leer()
    for posicion, registro in enumerate(datos):
        if registro["id"] == objeto.id:
            datos[posicion] = objeto.a_diccionario()
            return gestor.guardar(datos)
    return False


def eliminar(gestor, id_registro):
    datos = gestor.leer()
    for registro in datos:
        if registro["id"] == id_registro:
            datos.remove(registro)
            return gestor.guardar(datos)
    return False


def ids_registrados(gestor):
    # SET: permite comprobar si un identificador existe, sin repetir ids.
    return {datos["id"] for datos in gestor.leer()}


def indice_por_id(objetos):
    # DICT: relaciona cada id con su objeto para consultarlo directamente.
    return {objeto.id: objeto for objeto in objetos}


# =====================================================================
# ESTUDIANTES
# =====================================================================
def carnets_registrados(excepto_id=None):
    # SET: reúne los carnets para evitar que dos estudiantes usen el mismo.
    return {r["carnet"].upper() for r in gestor_estudiantes.leer()
            if r["id"] != excepto_id}


def validar_estudiante(datos, id_actual=None):
    for campo in ("nombre", "apellido", "email", "carnet"):
        if id_actual is None or campo in datos:
            if str(datos.get(campo) or "").strip() == "":
                return f"El campo {campo} es obligatorio"

    if "email" in datos:
        email = str(datos["email"]).strip().lower()
        if not es_email_valido(email):
            return "El email no es válido"
        # SET: los emails usados permiten detectar un correo repetido.
        emails = {e.email.lower() for e in obtener_estudiantes() if e.id != id_actual}
        if email in emails:
            return "Ese email ya está registrado"

    if "carnet" in datos:
        carnet = str(datos["carnet"]).strip().upper()
        if carnet in carnets_registrados(id_actual):
            return "Ese carnet ya está registrado"
    return None


def crear_estudiante(datos):
    error = validar_estudiante(datos)
    # TUPLA: devolvemos juntos el resultado y su mensaje a la vista.
    if error:
        return False, error

    estudiante = Estudiante(
        siguiente_id(gestor_estudiantes),
        str(datos["nombre"]).strip().title(),
        str(datos["apellido"]).strip().title(),
        str(datos["email"]).strip().lower(),
        str(datos["carnet"]).strip().upper(),
        str(datos.get("carrera", "")).strip().title()
    )
    if not guardar_nuevo(gestor_estudiantes, estudiante):
        return False, "No se pudo guardar el estudiante"
    return True, f"Estudiante creado: {estudiante.etiqueta()}"


def obtener_estudiantes():
    return leer_objetos(gestor_estudiantes, Estudiante)


def obtener_estudiante(id_estudiante):
    return obtener_por_id(gestor_estudiantes, Estudiante, id_estudiante)


def buscar_estudiantes(termino):
    # TUPLA: los campos de búsqueda son fijos y no necesitamos modificarlos.
    campos = ("nombre", "apellido", "email", "carnet", "carrera")
    return buscar(gestor_estudiantes, Estudiante, termino, campos)


def actualizar_estudiante(id_estudiante, cambios):
    estudiante = obtener_estudiante(id_estudiante)
    if estudiante is None:
        return False, "No existe ese estudiante"
    if not cambios:
        return False, "No se indicó ningún cambio"

    # SET: la diferencia deja únicamente los campos que no están permitidos.
    permitidos = {"nombre", "apellido", "email", "carnet", "carrera"}
    if set(cambios) - permitidos:
        return False, "Hay campos que no pertenecen a un estudiante"
    error = validar_estudiante(cambios, id_estudiante)
    if error:
        return False, error

    for campo, valor in cambios.items():
        valor = str(valor).strip()
        if campo in ("nombre", "apellido", "carrera"):
            valor = valor.title()
        elif campo == "email":
            valor = valor.lower()
        elif campo == "carnet":
            valor = valor.upper()
        setattr(estudiante, campo, valor)

    if not reemplazar(gestor_estudiantes, estudiante):
        return False, "No se pudo actualizar el estudiante"
    return True, f"Estudiante {id_estudiante} actualizado"


def eliminar_estudiante(id_estudiante):
    if obtener_estudiante(id_estudiante) is None:
        return False, "No existe ese estudiante"
    for matricula in obtener_matriculas():
        if matricula.estudiante_id == id_estudiante:
            return False, "Primero debe retirar las matrículas de este estudiante"
    if not eliminar(gestor_estudiantes, id_estudiante):
        return False, "No se pudo eliminar el estudiante"
    return True, f"Estudiante {id_estudiante} eliminado"


# =====================================================================
# MATERIAS
# =====================================================================
def codigos_registrados(excepto_id=None):
    # SET: evita registrar el mismo código de materia más de una vez.
    return {r["codigo"].upper() for r in gestor_materias.leer()
            if r["id"] != excepto_id}


def validar_materia(datos, id_actual=None):
    for campo in ("nombre", "codigo", "creditos"):
        if id_actual is None or campo in datos:
            if str(datos.get(campo) or "").strip() == "":
                return f"El campo {campo} es obligatorio"

    if "codigo" in datos:
        codigo = str(datos["codigo"]).strip().upper()
        if codigo in codigos_registrados(id_actual):
            return "Ese código ya está registrado"

    if "creditos" in datos:
        try:
            creditos = int(str(datos["creditos"]))
        except (TypeError, ValueError):
            return "Los créditos deben ser un número entero"
        if not 1 <= creditos <= 10:
            return "Los créditos deben estar entre 1 y 10"

    if "cupos" in datos:
        try:
            cupos = int(str(datos["cupos"]))
        except (TypeError, ValueError):
            return "Los cupos deben ser un número entero"
        if not 0 <= cupos <= Materia.CUPOS_MAXIMOS:
            return f"Los cupos deben estar entre 0 y {Materia.CUPOS_MAXIMOS}"

        # Los lugares ocupados también cuentan para el máximo de la materia.
        ocupados = 0
        for matricula in obtener_matriculas():
            if matricula.materia_id == id_actual:
                ocupados += 1
        if cupos + ocupados > Materia.CUPOS_MAXIMOS:
            return f"Con {ocupados} matrículas, puede dejar como máximo {Materia.CUPOS_MAXIMOS - ocupados} cupos"
    return None


def crear_materia(datos):
    error = validar_materia(datos)
    if error:
        return False, error
    materia = Materia(
        siguiente_id(gestor_materias),
        str(datos["nombre"]).strip(),
        str(datos["codigo"]).strip().upper(),
        int(datos["creditos"]),
        int(datos.get("cupos", Materia.CUPOS_MAXIMOS))
    )
    if not guardar_nuevo(gestor_materias, materia):
        return False, "No se pudo guardar la materia"
    return True, f"Materia creada: {materia.etiqueta()}"


def obtener_materias():
    return leer_objetos(gestor_materias, Materia)


def obtener_materia(id_materia):
    return obtener_por_id(gestor_materias, Materia, id_materia)


def buscar_materias(termino):
    # TUPLA: se busca siempre en estos dos campos.
    campos = ("nombre", "codigo")
    return buscar(gestor_materias, Materia, termino, campos)


def actualizar_materia(id_materia, cambios):
    materia = obtener_materia(id_materia)
    if materia is None:
        return False, "No existe esa materia"
    if not cambios:
        return False, "No se indicó ningún cambio"
    # SET: comprobamos que los campos enviados pertenezcan a una materia.
    if set(cambios) - {"nombre", "codigo", "creditos", "cupos"}:
        return False, "Hay campos que no pertenecen a una materia"
    error = validar_materia(cambios, id_materia)
    if error:
        return False, error

    if "nombre" in cambios:
        materia.nombre = str(cambios["nombre"]).strip()
    if "codigo" in cambios:
        materia.codigo = str(cambios["codigo"]).strip().upper()
    if "creditos" in cambios:
        materia.creditos = int(cambios["creditos"])
    if "cupos" in cambios:
        materia.cupos = int(cambios["cupos"])
    if not reemplazar(gestor_materias, materia):
        return False, "No se pudo actualizar la materia"
    return True, f"Materia {id_materia} actualizada"


def eliminar_materia(id_materia):
    if obtener_materia(id_materia) is None:
        return False, "No existe esa materia"
    for matricula in obtener_matriculas():
        if matricula.materia_id == id_materia:
            return False, "Primero debe retirar las matrículas de esta materia"
    if not eliminar(gestor_materias, id_materia):
        return False, "No se pudo eliminar la materia"
    return True, f"Materia {id_materia} eliminada"


def materias_sin_cupo():
    sin_cupo = []
    for materia in obtener_materias():
        if not materia.hay_cupo():
            sin_cupo.append(materia)
    return sin_cupo


# =====================================================================
# MATRÍCULAS
# =====================================================================
def validar_matricula(datos):
    try:
        estudiante_id = int(str(datos.get("estudiante_id", "")))
        materia_id = int(str(datos.get("materia_id", "")))
    except (TypeError, ValueError):
        return "Los identificadores deben ser números enteros"

    # SET: comprobamos la existencia de los ids antes de relacionar los datos.
    if estudiante_id not in ids_registrados(gestor_estudiantes):
        return "No existe ese estudiante"
    if materia_id not in ids_registrados(gestor_materias):
        return "No existe esa materia"

    periodo = str(datos.get("periodo") or "").strip()
    if periodo == "":
        return "El período es obligatorio"
    if not Materia.es_nota_valida(datos.get("nota", 0)):
        return "La nota debe ser un número entre 0 y 20"

    for matricula in obtener_matriculas():
        if (matricula.estudiante_id == estudiante_id
                and matricula.materia_id == materia_id
                and matricula.periodo == periodo):
            return "El estudiante ya está matriculado en esa materia y período"

    materia = obtener_materia(materia_id)
    if not materia.hay_cupo():
        return "La materia no tiene cupos disponibles"
    return None


def crear_matricula(datos):
    error = validar_matricula(datos)
    if error:
        return False, error

    materia = obtener_materia(int(datos["materia_id"]))
    matricula = Matricula(
        siguiente_id(gestor_matriculas),
        int(datos["estudiante_id"]),
        materia.id,
        str(datos["periodo"]).strip(),
        float(datos.get("nota", 0))
    )

    materia.ocupar_cupo()
    if not reemplazar(gestor_materias, materia):
        return False, "No se pudo guardar el cambio de cupos"
    if not guardar_nuevo(gestor_matriculas, matricula):
        # Si no se guarda la matrícula, devolvemos el cupo descontado.
        materia.liberar_cupo()
        if not reemplazar(gestor_materias, materia):
            return False, "No se guardó la matrícula y no se pudo restaurar el cupo"
        return False, "No se pudo guardar la matrícula"
    return True, f"Matrícula {matricula.id} registrada"


def obtener_matriculas():
    return leer_objetos(gestor_matriculas, Matricula)


def obtener_matricula(id_matricula):
    return obtener_por_id(gestor_matriculas, Matricula, id_matricula)


def registrar_nota(id_matricula, nota):
    matricula = obtener_matricula(id_matricula)
    if matricula is None:
        return False, "No existe esa matrícula"
    if not Materia.es_nota_valida(nota):
        return False, "La nota debe ser un número entre 0 y 20"

    matricula.nota = float(nota)
    if not reemplazar(gestor_matriculas, matricula):
        return False, "No se pudo guardar la nota"
    return True, f"Nota registrada: {matricula.nota:g} · {matricula.estado()}"


def retirar_matricula(id_matricula):
    matricula = obtener_matricula(id_matricula)
    if matricula is None:
        return False, "No existe esa matrícula"
    materia = obtener_materia(matricula.materia_id)
    if materia is None:
        return False, "No existe la materia de esta matrícula"
    if materia.cupos >= Materia.CUPOS_MAXIMOS:
        return False, "Revise los cupos de la materia: ya tiene el máximo disponible"

    materia.liberar_cupo()
    if not reemplazar(gestor_materias, materia):
        return False, "No se pudo guardar la devolución del cupo"
    if not eliminar(gestor_matriculas, id_matricula):
        # Si falla el retiro, el estudiante conserva su lugar.
        materia.ocupar_cupo()
        if not reemplazar(gestor_materias, materia):
            return False, "No se retiró la matrícula y no se pudo restaurar el cupo"
        return False, "No se pudo retirar la matrícula"
    return True, f"Matrícula {id_matricula} retirada y cupo devuelto"


def certificado(id_matricula):
    matricula = obtener_matricula(id_matricula)
    if matricula is None:
        return None

    # DICT ÍNDICE: accedemos a cada objeto por su id para armar el certificado.
    estudiantes = indice_por_id(obtener_estudiantes())
    materias = indice_por_id(obtener_materias())
    estudiante = estudiantes.get(matricula.estudiante_id)
    materia = materias.get(matricula.materia_id)
    if estudiante is None or materia is None:
        return "Faltan los datos del estudiante o de la materia"

    texto = f"CERTIFICADO #{matricula.id}   periodo: {matricula.periodo}\n\n"
    texto += f"Estudiante: {estudiante.nombre_completo()} ({estudiante.carnet})\n"
    texto += f"Materia   : {materia.nombre} ({materia.codigo}) · {materia.creditos} créditos\n\n"
    texto += "-" * 42 + "\n"
    texto += f"Nota      : {matricula.nota:g}\n"
    texto += f"Estado    : {matricula.estado()}"
    return texto


def matriculas_por_estudiante():
    # DICCIONARIO DE LISTAS: cada estudiante tiene su propia lista de matrículas.
    agrupadas = {}
    for matricula in obtener_matriculas():
        agrupadas.setdefault(matricula.estudiante_id, []).append(matricula)
    return agrupadas


def promedio_de_estudiante(id_estudiante):
    matriculas = matriculas_por_estudiante().get(id_estudiante, [])
    if not matriculas:
        return 0.0
    total = 0
    for matricula in matriculas:
        total += matricula.nota
    return round(total / len(matriculas), 2)
