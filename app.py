import os
from flask import Flask, render_template, redirect, request, session, url_for
from flask_mysqldb import MySQL
from flask_graphql import GraphQLView
import graphene
from graphene import ObjectType, String, Int, Field, List

app = Flask(__name__, template_folder='template')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'Usuarios'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['UPLOAD_FOLDER'] = 'uploads'

mysql = MySQL(app)


class PastelType(ObjectType):
    id = Int()
    foto = String()
    nombre = String()
    descripcion = String()
    precio = String()


class Query(ObjectType):
    pasteles = List(PastelType)

    def resolve_pasteles(self, info):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM pasteles")
        pasteles = cur.fetchall()
        cur.close()
        return [PastelType(**pastel) for pastel in pasteles]


class CreatePastel(graphene.Mutation):
    class Arguments:
        foto = String()
        nombre = String()
        descripcion = String()
        precio = String()

    ok = String()
    pastel = Field(lambda: PastelType)

    def mutate(self, info, foto, nombre, descripcion, precio):
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO pasteles (foto, nombre, descripcion, precio) VALUES (%s, %s, %s, %s)",
                    (foto, nombre, descripcion, precio))
        mysql.connection.commit()
        pastel = PastelType(foto=foto, nombre=nombre, descripcion=descripcion, precio=precio)
        return CreatePastel(ok="Pastel creado exitosamente", pastel=pastel)


class Mutation(ObjectType):
    create_pastel = CreatePastel.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))


@app.route("/")
def home():
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'pan1.jpg')
    return render_template('index.html')


# función login
@app.route('/acceso-login', methods=["GET", "POST"])
def login():
    if request.method == 'POST' and 'correo' in request.form and 'contraseña':
        _correo = request.form['correo']
        _password = request.form['contraseña']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE correo = %s AND contraseña = %s', (_correo, _password,))
        account = cur.fetchone()

        if account:
            session['logueado'] = True
            session['id'] = account['id']
            session['id_rol'] = account['id_rol']
            if session['id_rol'] == 1:
                return redirect(url_for('mostrar'))
            elif session['id_rol'] == 2:
                return redirect(url_for('mostraradmin'))
        else:
            return render_template('index.html', error="Usuario o Contraseña incorrecta, intente denuevo")


@app.route('/registro')
def registro():
    return render_template('registro.html')


@app.route('/crear-registro', methods=["GET", "POST"])
def crear_registro():
    correo = request.form['correo']
    contraseña = request.form['contraseña']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO usuarios (correo, contraseña, id_rol) VALUES (%s, %s, '1')", (correo, contraseña))
    mysql.connection.commit()

    return render_template('index.html', mensaje="Se registró exitosamente :)")


@app.route('/inicio')
def inicio():
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'inicio_fondo.png')
    return render_template('inicio.html')


@app.route('/carrito')
def carrito():
    return render_template('carrito.html')


@app.route('/agregar_pasteles')
def agregar_pasteles():
    return render_template('administrador_agregar.html')


@app.route('/administrador', methods=["GET", "POST"])
def mostraradmin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pasteles")
    pasteles = cur.fetchall()
    cur.close()
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'base.png')
    return render_template("administrador.html", pasteles=pasteles)


@app.route('/usuario', methods=["GET", "POST"])
def mostrar():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pasteles")
    pasteles = cur.fetchall()
    cur.close()
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'base.png')
    return render_template("usuario.html", pasteles=pasteles)


@app.route('/crear-pastel', methods=["GET", "POST"])
def crear_pastel():
    foto = request.files['foto']
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']

    foto.save('static/uploads/' + foto.filename)

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO pasteles (foto, nombre, descripcion, precio) VALUES (%s, %s, %s, %s)",
                (foto.filename, nombre, descripcion, precio))
    mysql.connection.commit()

    return redirect(url_for('mostraradmin'))


@app.route('/delete/<string:id>')
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM pasteles WHERE id= {0}".format(id))
    mysql.connection.commit()
    return redirect(url_for('mostraradmin'))


@app.route('/edit/<string:id>')
def edit(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pasteles WHERE id = %s", (id,))
    pastel = cur.fetchone()
    cur.close()
    return render_template('administrador_editar.html', pastel=pastel)


@app.route('/update/<string:id>', methods=['POST'])
def update(id):
    foto = request.files['foto']
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']

    cur = mysql.connection.cursor()
    cur.execute("UPDATE pasteles SET foto = %s, nombre = %s, descripcion = %s, precio = %s WHERE id = %s",
                (foto.filename, nombre, descripcion, precio, id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('mostraradmin'))


if __name__ == '__main__':
    app.secret_key = "Trabajo_Desarrollo"
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
