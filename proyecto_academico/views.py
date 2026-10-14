from abc import ABC, abstractmethod
import os

from models import Estudiante, Materia, Matricula
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido


CARPETA_DATOS = os.path.join(os.path.dirname(__file__), "data")


# La clase abstracta define qué operaciones debe tener cada controlador.
class CrudBase(ABC):

    @abstractmethod
    def leer(self):
        pass

    @abstractmethod
    def obtener(self, id_registro):
        pass

    @abstractmethod
    def buscar(self, texto):
        pass

    @abstractmethod
    def siguiente(self):
        pass

    @abstractmethod
    def crear(self, datos):
        pass

    @abstractmethod
    def actualizar(self, id_registro, datos):
        pass

    @abstractmethod
    def eliminar(self, id_registro):
        pass


class EstudianteController(CrudBase):
    def __init__(self, archivo=None):
        if archivo is None:
            archivo = os.path.join(CARPETA_DATOS, "estudiantes.json")
        self.gestor = GestorJSON(archivo)
        ruta_matriculas = os.path.join(os.path.dirname(archivo), "matriculas.json")
        self.gestor_matriculas = GestorJSON(ruta_matriculas)

    def siguiente(self):
        mayor = 0
        for datos in self.gestor.leer():
            if datos["id"] > mayor:
                mayor = datos["id"]
        return mayor + 1

    def leer(self):
        estudiantes = []
        for datos in self.gestor.leer():
            estudiantes.append(Estudiante.desde_diccionario(datos))
        return estudiantes

    def obtener(self, id_estudiante):
        for estudiante in self.leer():
            if estudiante.id == id_estudiante:
                return estudiante
        return None

    def buscar(self, termino):
        # TUPLA: los campos de búsqueda son fijos y no necesitamos modificarlos.
        campos = ("nombre", "apellido", "email", "carnet", "carrera")
        termino = termino.strip().lower()
        encontrados = []
        if termino == "":
            return encontrados
        for estudiante in self.leer():
            for campo in campos:
                if termino in str(getattr(estudiante, campo)).lower():
                    encontrados.append(estudiante)
                    break
        return encontrados

    def crear(self, datos):
        error = self.validar(datos)
        # TUPLA: devolvemos juntos el resultado y su mensaje a la vista.
        if error:
            return False, error

        estudiante = Estudiante(
            self.siguiente(),
            str(datos["nombre"]).strip().title(),
            str(datos["apellido"]).strip().title(),
            str(datos["email"]).strip().lower(),
            str(datos["carnet"]).strip().upper(),
            str(datos.get("carrera", "")).strip().title()
        )
        registros = self.gestor.leer()
        registros.append(estudiante.a_diccionario())
        if not self.gestor.guardar(registros):
            return False, "No se pudo guardar el estudiante"
        return True, f"Estudiante creado: {estudiante.etiqueta()}"

    def actualizar(self, id_estudiante, cambios):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, "No existe ese estudiante"
        if not cambios:
            return False, "No se indicó ningún cambio"

        # SET: la diferencia deja únicamente los campos que no están permitidos.
        permitidos = {"nombre", "apellido", "email", "carnet", "carrera"}
        if set(cambios) - permitidos:
            return False, "Hay campos que no pertenecen a un estudiante"
        error = self.validar(cambios, id_estudiante)
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

        registros = self.gestor.leer()
        for posicion, registro in enumerate(registros):
            if registro["id"] == id_estudiante:
                registros[posicion] = estudiante.a_diccionario()
                break
        if not self.gestor.guardar(registros):
            return False, "No se pudo actualizar el estudiante"
        return True, f"Estudiante {id_estudiante} actualizado"

    def eliminar(self, id_estudiante):
        if self.obtener(id_estudiante) is None:
            return False, "No existe ese estudiante"
        for matricula in self.gestor_matriculas.leer():
            if matricula["estudiante_id"] == id_estudiante:
                return False, "Primero debe retirar las matrículas de este estudiante"
        registros = self.gestor.leer()
        registros = [r for r in registros if r["id"] != id_estudiante]
        if not self.gestor.guardar(registros):
            return False, "No se pudo eliminar el estudiante"
        return True, f"Estudiante {id_estudiante} eliminado"

    def carnets_registrados(self, excepto_id=None):
        # SET: reúne los carnets para evitar que dos estudiantes usen el mismo.
        return {r["carnet"].upper() for r in self.gestor.leer()
                if r["id"] != excepto_id}

    def validar(self, datos, id_actual=None):
        for campo in ("nombre", "apellido", "email", "carnet"):
            if id_actual is None or campo in datos:
                if str(datos.get(campo) or "").strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return "El email no es válido"
            # SET: los emails usados permiten detectar un correo repetido.
            emails = {e.email.lower() for e in self.leer() if e.id != id_actual}
            if email in emails:
                return "Ese email ya está registrado"

        if "carnet" in datos:
            carnet = str(datos["carnet"]).strip().upper()
            if carnet in self.carnets_registrados(id_actual):
                return "Ese carnet ya está registrado"
        return None


class MateriaController(CrudBase):
    def __init__(self, archivo=None):
        if archivo is None:
            archivo = os.path.join(CARPETA_DATOS, "materias.json")
        self.gestor = GestorJSON(archivo)
        ruta_matriculas = os.path.join(os.path.dirname(archivo), "matriculas.json")
        self.gestor_matriculas = GestorJSON(ruta_matriculas)

    def siguiente(self):
        mayor = 0
        for datos in self.gestor.leer():
            if datos["id"] > mayor:
                mayor = datos["id"]
        return mayor + 1

    def leer(self):
        materias = []
        for datos in self.gestor.leer():
            materias.append(Materia.desde_diccionario(datos))
        return materias

    def obtener(self, id_materia):
        for materia in self.leer():
            if materia.id == id_materia:
                return materia
        return None

    def buscar(self, termino):
        # TUPLA: se busca siempre en estos dos campos.
        campos = ("nombre", "codigo")
        termino = termino.strip().lower()
        encontrados = []
        if termino == "":
            return encontrados
        for materia in self.leer():
            for campo in campos:
                if termino in str(getattr(materia, campo)).lower():
                    encontrados.append(materia)
                    break
        return encontrados

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        materia = Materia(
            self.siguiente(),
            str(datos["nombre"]).strip(),
            str(datos["codigo"]).strip().upper(),
            int(datos["creditos"]),
            int(datos.get("cupos", Materia.CUPOS_MAXIMOS))
        )
        registros = self.gestor.leer()
        registros.append(materia.a_diccionario())
        if not self.gestor.guardar(registros):
            return False, "No se pudo guardar la materia"
        return True, f"Materia creada: {materia.etiqueta()}"

    def actualizar(self, id_materia, cambios):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, "No existe esa materia"
        if not cambios:
            return False, "No se indicó ningún cambio"
        # SET: comprobamos que los campos enviados pertenezcan a una materia.
        if set(cambios) - {"nombre", "codigo", "creditos", "cupos"}:
            return False, "Hay campos que no pertenecen a una materia"
        error = self.validar(cambios, id_materia)
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
        registros = self.gestor.leer()
        for posicion, registro in enumerate(registros):
            if registro["id"] == id_materia:
                registros[posicion] = materia.a_diccionario()
                break
        if not self.gestor.guardar(registros):
            return False, "No se pudo actualizar la materia"
        return True, f"Materia {id_materia} actualizada"

    def eliminar(self, id_materia):
        if self.obtener(id_materia) is None:
            return False, "No existe esa materia"
        for matricula in self.gestor_matriculas.leer():
            if matricula["materia_id"] == id_materia:
                return False, "Primero debe retirar las matrículas de esta materia"
        registros = self.gestor.leer()
        registros = [r for r in registros if r["id"] != id_materia]
        if not self.gestor.guardar(registros):
            return False, "No se pudo eliminar la materia"
        return True, f"Materia {id_materia} eliminada"

    def materias_sin_cupo(self):
        sin_cupo = []
        for materia in self.leer():
            if not materia.hay_cupo():
                sin_cupo.append(materia)
        return sin_cupo

    def codigos_registrados(self, excepto_id=None):
        # SET: evita registrar el mismo código de materia más de una vez.
        return {r["codigo"].upper() for r in self.gestor.leer()
                if r["id"] != excepto_id}

    def validar(self, datos, id_actual=None):
        for campo in ("nombre", "codigo", "creditos"):
            if id_actual is None or campo in datos:
                if str(datos.get(campo) or "").strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "codigo" in datos:
            codigo = str(datos["codigo"]).strip().upper()
            if codigo in self.codigos_registrados(id_actual):
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
            for matricula in self.gestor_matriculas.leer():
                if matricula["materia_id"] == id_actual:
                    ocupados += 1
            if cupos + ocupados > Materia.CUPOS_MAXIMOS:
                return f"Con {ocupados} matrículas, puede dejar como máximo {Materia.CUPOS_MAXIMOS - ocupados} cupos"
        return None


class MatriculaController(CrudBase):
    def __init__(self, estudiantes, materias, archivo=None):
        self.estudiantes = estudiantes
        self.materias = materias
        if archivo is None:
            archivo = os.path.join(os.path.dirname(estudiantes.gestor.ruta), "matriculas.json")
        self.gestor = GestorJSON(archivo)
        # Los tres controladores consultan el mismo archivo de matrículas.
        self.estudiantes.gestor_matriculas = self.gestor
        self.materias.gestor_matriculas = self.gestor

    def siguiente(self):
        mayor = 0
        for datos in self.gestor.leer():
            if datos["id"] > mayor:
                mayor = datos["id"]
        return mayor + 1

    def buscar(self, texto):
        # TUPLA: el período y la fecha son los campos fijos de búsqueda.
        campos = ("periodo", "fecha")
        texto = texto.strip().lower()
        encontradas = []
        if texto == "":
            return encontradas
        for matricula in self.leer():
            for campo in campos:
                if texto in str(getattr(matricula, campo)).lower():
                    encontradas.append(matricula)
                    break
        return encontradas

    def actualizar(self, id_matricula, datos):
        if not datos:
            return False, "No se indicó ningún cambio"
        # SET: una matrícula solo permite actualizar el campo nota.
        if set(datos) != {"nota"}:
            return False, "Solo se puede actualizar la nota de una matrícula"
        return self.registrar_nota(id_matricula, datos["nota"])

    def leer(self):
        matriculas = []
        for datos in self.gestor.leer():
            matriculas.append(Matricula.desde_diccionario(datos))
        return matriculas

    def obtener(self, id_matricula):
        for matricula in self.leer():
            if matricula.id == id_matricula:
                return matricula
        return None

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        materia = self.materias.obtener(int(datos["materia_id"]))
        matricula = Matricula(
            self.siguiente(),
            int(datos["estudiante_id"]),
            materia.id,
            str(datos["periodo"]).strip(),
            float(datos.get("nota", 0))
        )

        materia.ocupar_cupo()
        registros_materias = self.materias.gestor.leer()
        for posicion, registro in enumerate(registros_materias):
            if registro["id"] == materia.id:
                registros_materias[posicion] = materia.a_diccionario()
                break
        if not self.materias.gestor.guardar(registros_materias):
            return False, "No se pudo guardar el cambio de cupos"
        registros = self.gestor.leer()
        registros.append(matricula.a_diccionario())
        if not self.gestor.guardar(registros):
            # Si no se guarda la matrícula, devolvemos el cupo descontado.
            materia.liberar_cupo()
            registros_materias = self.materias.gestor.leer()
            for posicion, registro in enumerate(registros_materias):
                if registro["id"] == materia.id:
                    registros_materias[posicion] = materia.a_diccionario()
                    break
            if not self.materias.gestor.guardar(registros_materias):
                return False, "No se guardó la matrícula y no se pudo restaurar el cupo"
            return False, "No se pudo guardar la matrícula"
        return True, f"Matrícula {matricula.id} registrada"

    def eliminar(self, id_matricula):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, "No existe esa matrícula"
        materia = self.materias.obtener(matricula.materia_id)
        if materia is None:
            return False, "No existe la materia de esta matrícula"
        if materia.cupos >= Materia.CUPOS_MAXIMOS:
            return False, "Revise los cupos de la materia: ya tiene el máximo disponible"

        materia.liberar_cupo()
        registros_materias = self.materias.gestor.leer()
        for posicion, registro in enumerate(registros_materias):
            if registro["id"] == materia.id:
                registros_materias[posicion] = materia.a_diccionario()
                break
        if not self.materias.gestor.guardar(registros_materias):
            return False, "No se pudo guardar la devolución del cupo"
        registros = self.gestor.leer()
        registros = [r for r in registros if r["id"] != id_matricula]
        if not self.gestor.guardar(registros):
            # Si falla el retiro, el estudiante conserva su lugar.
            materia.ocupar_cupo()
            registros_materias = self.materias.gestor.leer()
            for posicion, registro in enumerate(registros_materias):
                if registro["id"] == materia.id:
                    registros_materias[posicion] = materia.a_diccionario()
                    break
            if not self.materias.gestor.guardar(registros_materias):
                return False, "No se retiró la matrícula y no se pudo restaurar el cupo"
            return False, "No se pudo retirar la matrícula"
        return True, f"Matrícula {id_matricula} retirada y cupo devuelto"

    def registrar_nota(self, id_matricula, nota):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, "No existe esa matrícula"
        if not Materia.es_nota_valida(nota):
            return False, "La nota debe ser un número entre 0 y 20"

        matricula.nota = float(nota)
        registros = self.gestor.leer()
        for posicion, registro in enumerate(registros):
            if registro["id"] == id_matricula:
                registros[posicion] = matricula.a_diccionario()
                break
        if not self.gestor.guardar(registros):
            return False, "No se pudo guardar la nota"
        return True, f"Nota registrada: {matricula.nota:g} · {matricula.estado()}"

    def validar(self, datos):
        try:
            estudiante_id = int(str(datos.get("estudiante_id", "")))
            materia_id = int(str(datos.get("materia_id", "")))
        except (TypeError, ValueError):
            return "Los identificadores deben ser números enteros"

        # SET: comprobamos la existencia de los ids antes de relacionar los datos.
        ids_estudiantes = {e.id for e in self.estudiantes.leer()}
        ids_materias = {m.id for m in self.materias.leer()}
        if estudiante_id not in ids_estudiantes:
            return "No existe ese estudiante"
        if materia_id not in ids_materias:
            return "No existe esa materia"

        periodo = str(datos.get("periodo") or "").strip()
        if periodo == "":
            return "El período es obligatorio"
        if not Materia.es_nota_valida(datos.get("nota", 0)):
            return "La nota debe ser un número entre 0 y 20"

        for matricula in self.leer():
            if (matricula.estudiante_id == estudiante_id
                    and matricula.materia_id == materia_id
                    and matricula.periodo == periodo):
                return "El estudiante ya está matriculado en esa materia y período"

        materia = self.materias.obtener(materia_id)
        if not materia.hay_cupo():
            return "La materia no tiene cupos disponibles"
        return None

    def certificado(self, id_matricula):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return None

        # DICT ÍNDICE: accedemos a cada objeto por su id para armar el certificado.
        estudiantes = {e.id: e for e in self.estudiantes.leer()}
        materias = {m.id: m for m in self.materias.leer()}
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

    def matriculas_por_estudiante(self):
        # DICCIONARIO DE LISTAS: cada estudiante tiene su propia lista de matrículas.
        agrupadas = {}
        for matricula in self.leer():
            agrupadas.setdefault(matricula.estudiante_id, []).append(matricula)
        return agrupadas

    def promedio_de_estudiante(self, id_estudiante):
        matriculas = self.matriculas_por_estudiante().get(id_estudiante, [])
        if not matriculas:
            return 0.0
        total = 0
        for matricula in matriculas:
            total += matricula.nota
        return round(total / len(matriculas), 2)


# Se crea un solo controlador de cada tipo y se comparten con main.py.
estudiantes = EstudianteController()
materias = MateriaController()
matriculas = MatriculaController(estudiantes, materias)


# Se conservan los nombres de funciones que solicita la tarea.
# Cada función llama al controlador correspondiente; las reglas están en él.
def crear_estudiante(datos):
    return estudiantes.crear(datos)


def obtener_estudiantes():
    return estudiantes.leer()


def obtener_estudiante(id_estudiante):
    return estudiantes.obtener(id_estudiante)


def buscar_estudiantes(termino):
    return estudiantes.buscar(termino)


def actualizar_estudiante(id_estudiante, cambios):
    return estudiantes.actualizar(id_estudiante, cambios)


def eliminar_estudiante(id_estudiante):
    return estudiantes.eliminar(id_estudiante)


def crear_materia(datos):
    return materias.crear(datos)


def obtener_materias():
    return materias.leer()


def obtener_materia(id_materia):
    return materias.obtener(id_materia)


def buscar_materias(termino):
    return materias.buscar(termino)


def actualizar_materia(id_materia, cambios):
    return materias.actualizar(id_materia, cambios)


def eliminar_materia(id_materia):
    return materias.eliminar(id_materia)


def materias_sin_cupo():
    return materias.materias_sin_cupo()


def crear_matricula(datos):
    return matriculas.crear(datos)


def obtener_matriculas():
    return matriculas.leer()


def obtener_matricula(id_matricula):
    return matriculas.obtener(id_matricula)


def registrar_nota(id_matricula, nota):
    return matriculas.registrar_nota(id_matricula, nota)


def retirar_matricula(id_matricula):
    return matriculas.eliminar(id_matricula)


def certificado(id_matricula):
    return matriculas.certificado(id_matricula)


def matriculas_por_estudiante():
    return matriculas.matriculas_por_estudiante()


def promedio_de_estudiante(id_estudiante):
    return matriculas.promedio_de_estudiante(id_estudiante)

