from flask import Flask, request, redirect, Response
import sqlite3
import os

app = Flask(__name__)
carpeta = os.path.dirname(os.path.abspath(__file__))
base = os.path.join(carpeta, "datos.db")
html = os.path.join(carpeta, "templates", "pagina.html")

def preparar_base():
    conexion = sqlite3.connect(base)
    cursor = conexion.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (id_usuario INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, email TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS podcasts (id_podcast INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, archivo TEXT, audio BLOB, id_usuario INTEGER)")
    cantidad = cursor.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if cantidad == 0:
        cursor.execute("INSERT INTO usuarios(nombre, email) VALUES('Luca', 'merk2dc@gmail.com')")
        cursor.execute("INSERT INTO usuarios(nombre, email) VALUES('Gonzalo', 'Gonchi@gmail.com')")
    conexion.commit()
    conexion.close()

def get_podcast_duration_estimate(podcast_id):
    """Estima duración basada en el ID (para demostración)"""
    durations = ["1:30", "2:05", "1:45", "3:10", "2:15", "1:50", "2:45", "1:20", "2:30", "1:55", "2:10", "3:05", "1:40", "2:20", "2:50"]
    return durations[podcast_id % len(durations)]

def generate_podcast_item(usuario, titulo, podcast_id):
    """Genera el HTML para un item de podcast con controles de reproducción"""
    duration = get_podcast_duration_estimate(podcast_id)
    return f'''
        <div class="podcast-item" data-audio-id="{podcast_id}" data-title="{titulo}" data-artist="{usuario}">
            <div class="waveform-icon">
                <svg viewBox="0 0 100 60" preserveAspectRatio="none">
                    <rect x="10" y="20" width="3" height="20"/>
                    <rect x="16" y="10" width="3" height="40"/>
                    <rect x="22" y="15" width="3" height="30"/>
                    <rect x="28" y="5" width="3" height="50"/>
                    <rect x="34" y="18" width="3" height="24"/>
                    <rect x="40" y="12" width="3" height="36"/>
                    <rect x="46" y="22" width="3" height="16"/>
                    <rect x="52" y="8" width="3" height="44"/>
                    <rect x="58" y="20" width="3" height="20"/>
                    <rect x="64" y="14" width="3" height="32"/>
                    <rect x="70" y="18" width="3" height="24"/>
                    <rect x="76" y="10" width="3" height="40"/>
                    <rect x="82" y="16" width="3" height="28"/>
                    <rect x="88" y="20" width="3" height="20"/>
                </svg>
            </div>
            <div class="podcast-info">
                <div class="podcast-duration">{duration}</div>
                <div class="podcast-controls">
                    <button class="control-play" title="Reproducir">
                        <i class="fas fa-play"></i>
                    </button>
                </div>
            </div>
        </div>
    '''

@app.route("/")
def inicio():
    preparar_base()
    conexion = sqlite3.connect(base)
    cursor = conexion.cursor()
    cursor.execute("SELECT id_podcast, usuarios.nombre, podcasts.titulo FROM podcasts INNER JOIN usuarios ON podcasts.id_usuario = usuarios.id_usuario ORDER BY podcasts.id_podcast DESC")
    lista = cursor.fetchall()
    

    usuarios = cursor.execute("SELECT id_usuario, nombre FROM usuarios").fetchall()
    conexion.close()
    

    opciones = ""
    for usuario in usuarios:
        opciones += f"<option value='{usuario[0]}'>{usuario[0]} - {usuario[1]}</option>"

    rows = []
    for i in range(0, len(lista), 5):
        row_items = ""
        row_podcasts = lista[i:i+5]
        for podcast in row_podcasts:
            podcast_id, usuario, titulo = podcast
            row_items += generate_podcast_item(usuario, titulo, podcast_id)
        rows.append(row_items)
    

    row1 = rows[0] if len(rows) > 0 else ""
    row2 = rows[1] if len(rows) > 1 else ""
    row3 = rows[2] if len(rows) > 2 else ""
    
    archivo = open(html, "r", encoding="utf-8")
    pagina = archivo.read()
    archivo.close()
    
    pagina = pagina.replace("PODCASTS_GRID_ROW_1", row1)
    pagina = pagina.replace("PODCASTS_GRID_ROW_2", row2)
    pagina = pagina.replace("PODCASTS_GRID_ROW_3", row3)
    pagina = pagina.replace("USUARIOS_AQUI", opciones)
    
    return pagina

@app.route("/guardar", methods=["POST"])
def guardar():
    usuario = request.form["usuario"]
    titulo = request.form["titulo"]
    audio = request.files["audio"]
    nombre = audio.filename
    if nombre == "" or not nombre.lower().endswith(".mp3"):
        return redirect("/")
    nombre = nombre.replace(" ", "_")
    datos = audio.read()
    conexion = sqlite3.connect(base)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO podcasts(titulo, archivo, audio, id_usuario) VALUES(?, ?, ?, ?)", (titulo, nombre, datos, usuario))
    conexion.commit()
    conexion.close()
    return redirect("/")

@app.route("/audio/<id>")
def escuchar(id):
    conexion = sqlite3.connect(base)
    cursor = conexion.cursor()
    cursor.execute("SELECT audio FROM podcasts WHERE id_podcast = ?", (id,))
    fila = cursor.fetchone()
    conexion.close()
    if fila == None:
        return redirect("/")
    return Response(fila[0], mimetype="audio/mpeg")

if __name__ == "__main__":
    preparar_base()
    app.run(debug=True)
