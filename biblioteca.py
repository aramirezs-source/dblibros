import sqlite3
import os
import re
import getpass

from usuari import Usuari, UsuariRegistrat

# --- Configuració base de dades ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "biblioteca.db")

conn = sqlite3.connect(DB)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuaris (
        dni TEXT PRIMARY KEY,
        nom TEXT NOT NULL,
        cognoms TEXT NOT NULL,
        contrasenya TEXT,
        tipus_usuari TEXT CHECK(tipus_usuari IN ('lector', 'admin'))
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS llibres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titol TEXT NOT NULL,
        autor TEXT NOT NULL,
        dni_prestec TEXT DEFAULT '0'
    )
""")

conn.commit()

# --- Validació DNI ---
def validar_dni(dni):
    patron = r'^\d{8}[A-HJ-NP-TV-Z]$'
    return re.match(patron, dni)

# --- Login ---
def login():
    print("\n--- LOGIN ---")
    dni = input("DNI: ").strip()
    contrasenya = getpass.getpass("Contrasenya: ").strip()

    cursor.execute("SELECT nom, cognoms, contrasenya, tipus_usuari FROM usuaris WHERE dni = ?", (dni,))
    usuari = cursor.fetchone()

    if usuari and usuari[2] == UsuariRegistrat()._encripta_contrasenya(contrasenya):
        print(f"Benvingut/da {usuari[0]} {usuari[1]} ({usuari[3]})")
        return {'dni': dni, 'nom': usuari[0], 'cognoms': usuari[1], 'tipus': usuari[3]}
    else:
        print("DNI o contrasenya incorrectes.")
        return None

# --- Classe Llibre ---
class Llibre:
    def __init__(self, titol, autor, dni_prestec='0'):
        self.titol = titol
        self.autor = autor
        self.dni_prestec = dni_prestec

    def guardar(self):
        cursor.execute("INSERT INTO llibres (titol, autor, dni_prestec) VALUES (?, ?, ?)",
                       (self.titol, self.autor, self.dni_prestec))
        conn.commit()
        print("Llibre afegit correctament.")

    @staticmethod
    def eliminar(id):
        cursor.execute("DELETE FROM llibres WHERE id = ?", (id,))
        conn.commit()
        print("Llibre eliminat correctament.")

    @staticmethod
    def actualitzar(id):
        cursor.execute("SELECT titol, autor FROM llibres WHERE id = ?", (id,))
        resultat = cursor.fetchone()
        if resultat:
            titol_actual, autor_actual = resultat
            nou_titol = input(f"Nou títol (enter per deixar '{titol_actual}'): ").strip() or titol_actual
            nou_autor = input(f"Nou autor (enter per deixar '{autor_actual}'): ").strip() or autor_actual
            cursor.execute("UPDATE llibres SET titol = ?, autor = ? WHERE id = ?", (nou_titol, nou_autor, id))
            conn.commit()
            print("Llibre actualitzat correctament.")
        else:
            print("Llibre no trobat.")

    @staticmethod
    def prestar(id, dni):
        cursor.execute("SELECT dni_prestec FROM llibres WHERE id = ?", (id,))
        resultat = cursor.fetchone()
        if resultat:
            if resultat[0] != '0':
                print("Aquest llibre ja està prestat.")
            else:
                cursor.execute("SELECT COUNT(*) FROM llibres WHERE dni_prestec = ?", (dni,))
                comptador = cursor.fetchone()[0]
                if comptador >= 3:
                    print("Aquest usuari ja té 3 llibres prestats.")
                else:
                    cursor.execute("UPDATE llibres SET dni_prestec = ? WHERE id = ?", (dni, id))
                    conn.commit()
                    print("Llibre prestat correctament.")
        else:
            print("Llibre no trobat.")

    @staticmethod
    def tornar(id):
        cursor.execute("SELECT dni_prestec FROM llibres WHERE id = ?", (id,))
        resultat = cursor.fetchone()
        if resultat:
            if resultat[0] == '0':
                print("Aquest llibre no està en préstec.")
            else:
                cursor.execute("UPDATE llibres SET dni_prestec = '0' WHERE id = ?", (id,))
                conn.commit()
                print("Llibre retornat correctament.")
        else:
            print("Llibre no trobat.")

# --- Funcions Auxiliars ---
def llistar_usuaris():
    cursor.execute("SELECT dni, nom, cognoms, tipus_usuari FROM usuaris")
    usuaris = cursor.fetchall()
    print("\n--- Usuaris ---")
    for u in usuaris:
        tipus = "Registrat" if u[3] else "No registrat"
        print(f"{u[1]} {u[2]} : {u[0]} ({tipus})")
    if not usuaris:
        print("No hi ha usuaris.")

def llistar_llibres():
    cursor.execute("SELECT * FROM llibres")
    llibres = cursor.fetchall()
    print("\n--- Llibres ---")
    for l in llibres:
        estat = f"PRESTAT a {l[3]}" if l[3] != '0' else "Disponible"
        print(f"ID: {l[0]}, Títol: {l[1]}, Autor: {l[2]}, Estat: {estat}")
    if not llibres:
        print("No hi ha llibres.")

# --- Menús segons tipus ---
def menu_admin():
    while True:
        print("\n--- Menú Admin ---")
        print("1. Afegir usuari bàsic")
        print("2. Afegir usuari registrat")
        print("3. Llistar usuaris")
        print("4. Eliminar usuari")
        print("5. Afegir llibre")
        print("6. Llistar llibres")
        print("7. Eliminar llibre")
        print("8. Prestar llibre")
        print("9. Tornar llibre")
        print("10. Actualitzar usuari")
        print("11. Actualitzar llibre")
        print("12. Sortir")

        opcio = input("Selecciona una opció: ")

        if opcio == '1':
            u = Usuari()
            u.introduir_dades()
            u.guardar(cursor, conn)
        elif opcio == '2':
            ur = UsuariRegistrat()
            ur.introduir_dades()
            ur.guardar(cursor, conn)
        elif opcio == '3':
            llistar_usuaris()
        elif opcio == '4':
            dni = input("DNI a eliminar: ")
            u = Usuari(dni=dni)
            u.eliminar(cursor, conn)
        elif opcio == '5':
            titol = input("Títol: ").strip()
            autor = input("Autor: ").strip()
            l = Llibre(titol, autor)
            l.guardar()
        elif opcio == '6':
            llistar_llibres()
        elif opcio == '7':
            id = input("ID del llibre: ")
            Llibre.eliminar(id)
        elif opcio == '8':
            id = input("ID llibre: ")
            dni = input("DNI lector: ")
            if validar_dni(dni):
                Llibre.prestar(id, dni)
            else:
                print("DNI no vàlid.")
        elif opcio == '9':
            id = input("ID llibre a tornar: ")
            Llibre.tornar(id)
        elif opcio == '10':
            dni = input("DNI: ")
            cursor.execute("SELECT * FROM usuaris WHERE dni = ?", (dni,))
            usuari = cursor.fetchone()
            if usuari:
                u = Usuari(usuari[1], usuari[2], dni)
                u.actualitzar(cursor, conn)
            else:
                print("Usuari no trobat.")
        elif opcio == '11':
            id = input("ID del llibre a actualitzar: ")
            Llibre.actualitzar(id)
        elif opcio == '12':
            print("Sortint...")
            break
        else:
            print("Opció no vàlida!")

def menu_lector(dni):
    while True:
        print("\n--- Menú Lector ---")
        print("1. Llistar llibres")
        print("2. Prestar llibre")
        print("3. Tornar llibre")
        print("4. Sortir")

        opcio = input("Selecciona una opció: ")

        if opcio == '1':
            llistar_llibres()
        elif opcio == '2':
            id = input("ID llibre a prestar: ")
            Llibre.prestar(id, dni)
        elif opcio == '3':
            id = input("ID llibre a tornar: ")
            Llibre.tornar(id)
        elif opcio == '4':
            print("Sortint...")
            break
        else:
            print("Opció no vàlida!")

# --- Execució ---
if __name__ == "__main__":
    usuari_actiu = None
    while not usuari_actiu:
        usuari_actiu = login()

    if usuari_actiu["tipus"] == "admin":
        menu_admin()
    else:
        menu_lector(usuari_actiu["dni"])

    conn.close()
