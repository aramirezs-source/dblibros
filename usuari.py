import re
import hashlib
import getpass

# Validació de DNI
def validar_dni(dni):
    patron = r'^\d{8}[A-HJ-NP-TV-Z]$'
    return re.match(patron, dni)

class Usuari:
    """
    Classe que representa un usuari de la biblioteca.

    Atributs:
        nom (str): Nom de l'usuari.
        cognoms (str): Cognoms de l'usuari.
        dni (str): DNI de l'usuari (clau primària).

    Mètodes:
        guardar(): Insereix l'usuari a la base de dades.
        eliminar(): Elimina l'usuari de la base de dades pel seu DNI.
        actualitzar(): Actualitza el nom i cognoms.
        imprimir_dades(): Mostra les dades de l'usuari.
        introduir_dades(): Demana les dades de l'usuari per consola.
    """
    def __init__(self, nom="None", cognoms="None", dni="None"):
        self.nom = nom
        self.cognoms = cognoms
        self.dni = dni    

    def guardar(self, cursor, conn):
        if not validar_dni(self.dni):
            print("Error: El DNI no és vàlid.")
            return
        try:
            tipus = getattr(self, 'tipus_usuari', 'lector')  # Usa lector si no está definido
            cursor.execute("INSERT INTO usuaris (dni, nom, cognoms, tipus_usuari) VALUES (?, ?, ?, ?)",
                        (self.dni, self.nom, self.cognoms, tipus))
            conn.commit()
            print("Usuari afegit correctament.")
        except sqlite3.IntegrityError:
            print("Error: Ja existeix un usuari amb aquest DNI.")


    def eliminar(self, cursor, conn):
        cursor.execute("DELETE FROM usuaris WHERE dni = ?", (self.dni,))
        conn.commit()
        print("Usuari eliminat correctament.")

    def actualitzar(self, cursor, conn):
        nou_nom = input("Nou nom (enter per deixar igual): ").strip() or self.nom
        nous_cognoms = input("Nous cognoms (enter per deixar igual): ").strip() or self.cognoms
        cursor.execute("UPDATE usuaris SET nom = ?, cognoms = ? WHERE dni = ?", (nou_nom, nous_cognoms, self.dni))
        conn.commit()
        print("Usuari actualitzat correctament.")

    def imprimir_dades(self):
        print(f"{self.nom} {self.cognoms} : {self.dni}")

    def introduir_dades(self):
        while True:
            self.nom = input("Introdueix el nom: ").strip()
            self.cognoms = input("Introdueix els cognoms: ").strip()
            self.dni = input("Introdueix el DNI: ").strip()
            if not self.nom or not self.cognoms or not self.dni:
                print("Error: Cap camp pot estar buit!")
            elif not validar_dni(self.dni):
                print("Error: DNI no vàlid (ex: 12345678A)")
            else:
                break


class UsuariRegistrat(Usuari):
    """
    Classe que representa un usuari registrat (lector o admin),
    que hereta d'Usuari i afegeix autenticació.

    Atributs:
        _contrasenya (str): Contrasenya encriptada.
        tipus_usuari (str): Pot ser "lector" o "admin".

    Mètodes:
        _encripta_contrasenya(clau): Retorna la clau encriptada.
        verificar_contrasenya(clau): Comprova si la clau introduïda coincideix.
        introduir_dades(): Demana dades personals + contrasenya i tipus.
        imprimir_dades(): Mostra les dades.
    """

    def __init__(self, nom="None", cognoms="None", dni="None", tipus_usuari="lector"):
        super().__init__(nom, cognoms, dni)
        self._contrasenya = None
        self.tipus_usuari = tipus_usuari if tipus_usuari in ["lector", "admin"] else "lector"

    def _encripta_contrasenya(self, contrasenya):
        return hashlib.sha256(contrasenya.encode()).hexdigest()

    def verificar_contrasenya(self, contrasenya):
        return self._contrasenya == self._encripta_contrasenya(contrasenya)

    def introduir_dades(self):
        super().introduir_dades()
        while True:
            contrasenya = getpass.getpass("Introdueix la contrasenya: ")
            repetir = getpass.getpass("Repeteix la contrasenya: ")
            if contrasenya != repetir:
                print("Error: Les contrasenyes no coincideixen.")
            elif len(contrasenya) < 4:
                print("Error: La contrasenya ha de tenir almenys 4 caràcters.")
            else:
                self._contrasenya = self._encripta_contrasenya(contrasenya)
                break

        tipus = input("Tipus d'usuari (lector/admin): ").strip().lower()
        if tipus in ["lector", "admin"]:
            self.tipus_usuari = tipus
        else:
            print("Tipus no vàlid, s'ha assignat 'lector' per defecte.")
            self.tipus_usuari = "lector"
    def guardar(self, cursor, conn):
        if not validar_dni(self.dni):
            print("Error: El DNI no és vàlid.")
            return
        try:
            cursor.execute(
                "INSERT INTO usuaris (dni, nom, cognoms, contrasenya, tipus_usuari) VALUES (?, ?, ?, ?, ?)",
                (self.dni, self.nom, self.cognoms, self._contrasenya, self.tipus_usuari)
            )
            conn.commit()
            print("Usuari registrat afegit correctament.")
        except:
            print("Error: Ja existeix un usuari amb aquest DNI.")

    def imprimir_dades(self):
        print(f"{self.nom} {self.cognoms} : {self.dni} ({self.tipus_usuari})")
