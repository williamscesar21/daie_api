from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text
from sqlalchemy.sql import func


# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/daie_pos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for all routes
CORS(app)

db = SQLAlchemy(app)

# Models
class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class Productos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    impuesto_venta = db.Column(db.Numeric(10, 2))
    impuesto_compra = db.Column(db.Numeric(10, 2))
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    referencia = db.Column(db.String(100))
    link_imagen = db.Column(db.String(255))
    categoria = db.relationship('Categoria', backref=db.backref('productos', lazy=True))

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(20), nullable=False)
    telefono = db.Column(db.String(20))
    nro_ordenes = db.Column(db.Integer, default=0)

class Mesero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class Mesas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(20), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    capacidad = db.Column(db.Integer, nullable=False)

class Ordenes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    total = db.Column(db.Numeric(10, 2))
    mesa = db.Column(db.String(20))
    estado = db.Column(db.String(20), nullable=False)
    mesero_id = db.Column(db.Integer, db.ForeignKey('mesero.id'), nullable=False)
    metodo_pago = db.Column(db.String(20))
    referencia_pago = db.Column(db.String(100))
    vuelto = db.Column(db.Numeric(10, 2))
    fecha = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    nota = db.Column(db.Text)

class OrdenesProductos(db.Model):
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), primary_key=True)
    producto_precio = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    orden_producto_total = db.Column(db.Numeric(10, 2), nullable=False)


class Sesion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(20), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class SesionOrdenes(db.Model):
    sesion_id = db.Column(db.Integer, db.ForeignKey('sesion.id'), primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), primary_key=True)
    sesion = db.relationship('Sesion', backref=db.backref('sesion_ordenes', cascade="all, delete-orphan"))
    orden = db.relationship('Ordenes', backref=db.backref('sesion_ordenes', cascade="all, delete-orphan"))

class Valoraciones(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text)
    calificacion = db.Column(db.Integer, nullable=False)  # Escala de 1 a 5, por ejemplo
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = db.relationship('Cliente', backref=db.backref('valoraciones', lazy=True))


# API Endpoints

@app.route('/', methods=['GET'])
def health_check():
    try:
        # Realiza una consulta simple para verificar la conexión a la base de datos
        db.session.execute(text('SELECT 1'))  # Usar text() para la consulta
        return jsonify({'message': 'API funcionando sin errores'}), 200
    except Exception as e:
        return jsonify({'error': 'API no funcionando', 'details': str(e)}), 500


    

#Categorias
@app.route('/categorias', methods=['GET', 'POST'])
def manage_categorias():
    try:
        if request.method == 'GET':
            categorias = Categoria.query.all()
            return jsonify([{'id': c.id, 'nombre': c.nombre} for c in categorias]), 200

        if request.method == 'POST':
            data = request.get_json()
            nueva_categoria = Categoria(nombre=data['nombre'])
            db.session.add(nueva_categoria)
            db.session.commit()
            return jsonify({'message': 'Categoría creada', 'id': nueva_categoria.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/categorias/<int:id>', methods=['PUT', 'DELETE'])
def manage_categoria(id):
    try:
        categoria = Categoria.query.get_or_404(id)

        if request.method == 'PUT':
            data = request.get_json()
            categoria.nombre = data['nombre']
            db.session.commit()
            return jsonify({'message': 'Categoría actualizada'}), 200

        if request.method == 'DELETE':
            db.session.delete(categoria)
            db.session.commit()
            return jsonify({'message': 'Categoría eliminada'}), 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#Productos
@app.route('/productos', methods=['GET', 'POST'])
def manage_productos():
    try:
        if request.method == 'GET':
            productos = Productos.query.all()
            return jsonify([{
                'id': p.id,
                'nombre': p.nombre,
                'precio_venta': float(p.precio_venta),
                # 'impuesto_venta': float(p.impuesto_venta),
                # 'impuesto_compra': float(p.impuesto_compra),
                'categoria_id': p.categoria_id,
                'referencia': p.referencia,
                'link_imagen': p.link_imagen
            } for p in productos]), 200

        if request.method == 'POST':
            data = request.get_json()
            nuevo_producto = Productos(
                nombre=data['nombre'],
                precio_venta=data['precio_venta'],
                impuesto_venta=data['impuesto_venta'],
                impuesto_compra=data['impuesto_compra'],
                categoria_id=data['categoria_id'],
                referencia=data['referencia'],
                link_imagen=data.get('link_imagen')
            )
            db.session.add(nuevo_producto)
            db.session.commit()
            return jsonify({'message': 'Producto creado', 'id': nuevo_producto.id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/productos/<int:id>', methods=['PUT', 'DELETE'])
def manage_producto(id):
    try:
        producto = Productos.query.get_or_404(id)

        if request.method == 'PUT':
            data = request.get_json()
            producto.nombre = data['nombre']
            producto.precio_venta = data['precio_venta']
            producto.impuesto_venta = data['impuesto_venta']
            producto.impuesto_compra = data['impuesto_compra']
            producto.categoria_id = data['categoria_id']
            producto.referencia = data['referencia']
            producto.link_imagen = data.get('link_imagen')
            db.session.commit()
            return jsonify({'message': 'Producto actualizado'}), 200

        if request.method == 'DELETE':
            db.session.delete(producto)
            db.session.commit()
            return jsonify({'message': 'Producto eliminado'}), 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#Clientes
@app.route('/clientes', methods=['GET', 'POST'])
def manage_clientes():
    try:
        if request.method == 'GET':
            clientes = Cliente.query.all()
            return jsonify([{
                'id': c.id,
                'nombre': c.nombre,
                'cedula': c.cedula,
                'telefono': c.telefono,
                'nro_ordenes': c.nro_ordenes
            } for c in clientes]), 200

        if request.method == 'POST':
            data = request.get_json()
            nuevo_cliente = Cliente(
                nombre=data['nombre'],
                cedula=data['cedula'],
                telefono=data['telefono'],
                nro_ordenes=data.get('nro_ordenes', 0)
            )
            db.session.add(nuevo_cliente)
            db.session.commit()
            return jsonify({'message': 'Cliente creado', 'id': nuevo_cliente.id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clientes/<int:id>', methods=['PUT', 'DELETE'])
def manage_cliente(id):
    try:
        cliente = Cliente.query.get_or_404(id)

        if request.method == 'PUT':
            data = request.get_json()
            cliente.nombre = data['nombre']
            cliente.cedula = data['cedula']
            cliente.telefono = data['telefono']
            cliente.nro_ordenes = data.get('nro_ordenes', cliente.nro_ordenes)
            db.session.commit()
            return jsonify({'message': 'Cliente actualizado'}), 200

        if request.method == 'DELETE':
            db.session.delete(cliente)
            db.session.commit()
            return jsonify({'message': 'Cliente eliminado'}), 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
#Obtener un cliente por su id
@app.route('/clientes/<int:id>', methods=['GET'])
def get_cliente(id):
    try:
        cliente = Cliente.query.get_or_404(id)  
        return jsonify({'id': cliente.id, 'nombre': cliente.nombre, 'cedula': cliente.cedula, 'telefono': cliente.telefono, 'nro_ordenes': cliente.nro_ordenes}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#Meseros
@app.route('/meseros', methods=['GET', 'POST'])
def manage_meseros():
    try:
        if request.method == 'GET':
            meseros = Mesero.query.all()
            return jsonify([{'id': m.id, 'nombre': m.nombre} for m in meseros]), 200

        if request.method == 'POST':
            data = request.get_json()
            nuevo_mesero = Mesero(nombre=data['nombre'])
            db.session.add(nuevo_mesero)
            db.session.commit()
            return jsonify({'message': 'Mesero creado', 'id': nuevo_mesero.id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/meseros/<int:id>', methods=['PUT', 'DELETE'])
def manage_mesero(id):
    try:
        mesero = Mesero.query.get_or_404(id)

        if request.method == 'PUT':
            data = request.get_json()
            mesero.nombre = data['nombre']
            db.session.commit()
            return jsonify({'message': 'Mesero actualizado'}), 200

        if request.method == 'DELETE':
            db.session.delete(mesero)
            db.session.commit()
            return jsonify({'message': 'Mesero eliminado'}), 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
#Mesas
@app.route('/mesas', methods=['GET', 'POST'])
def manage_mesas():
    try:
        if request.method == 'GET':
            mesas = Mesas.query.all()
            return jsonify([{'id': m.id, 'numero': m.numero, 'capacidad': m.capacidad, 'estado': m.estado} for m in mesas]), 200

        if request.method == 'POST':
            data = request.get_json()
            nueva_mesa = Mesas(numero=data['numero'], capacidad=data['capacidad'], estado=data['estado'])
            db.session.add(nueva_mesa)
            db.session.commit()
            return jsonify({'message': 'Mesa creada', 'id': nueva_mesa.id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
#Obtener mesa por id
@app.route('/mesas/<int:id>', methods=['GET'])
def get_mesa(id):
    try:
        mesa = Mesas.query.get_or_404(id)   
        return jsonify({'id': mesa.id, 'numero': mesa.numero, 'capacidad': mesa.capacidad, 'estado': mesa.estado}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#Actualizar el estado de la mesa
@app.route('/mesas/<int:id>', methods=['PUT'])
def manage_mesa(id):
    try:
        mesa = Mesas.query.get_or_404(id)

        data = request.get_json()
        mesa.estado = data['estado']
        db.session.commit()
        return jsonify({'message': 'Mesa actualizada'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Ordenes
@app.route('/ordenes', methods=['GET', 'POST'])
def manage_ordenes():
    try:
        if request.method == 'GET':
            ordenes = Ordenes.query.all()
            return jsonify([{
                'id': o.id,
                'cliente_id': o.cliente_id,
                'total': o.total,
                'mesa': o.mesa,
                'estado': o.estado,
                'mesero_id': o.mesero_id,
                'metodo_pago': o.metodo_pago,
                'referencia_pago': o.referencia_pago,
                'vuelto': o.vuelto,
                'fecha': o.fecha,
                'nota': o.nota
            } for o in ordenes]), 200

        if request.method == 'POST':
            data = request.get_json()
            print("Datos recibidos para nueva orden:", data)  # Agrega esta línea para depurar
            nueva_orden = Ordenes(
                cliente_id=data['cliente_id'],
                mesa=data.get('mesa'),
                estado=data['estado'],
                mesero_id=data.get('mesero_id')
            )
            db.session.add(nueva_orden)
            db.session.commit()
            return jsonify({'message': 'Orden creada', 'id': nueva_orden.id}), 201

    except Exception as e:
        print("Error al agregar orden:", str(e))  # Agrega esta línea para depurar
        return jsonify({'error': str(e)}), 500

@app.route('/ordenes/<int:id>', methods=['PUT', 'DELETE'])
def manage_orden(id):
    try:
        orden = Ordenes.query.get_or_404(id)

        if request.method == 'PUT':
            data = request.get_json()
            # Actualizar solo las propiedades que se envían en el cuerpo de la solicitud
            if 'cliente_id' in data:
                orden.cliente_id = data['cliente_id']
            if 'total' in data:
                orden.total = data['total']
            if 'mesa' in data:
                orden.mesa = data['mesa']
            if 'estado' in data:
                orden.estado = data['estado']
            if 'mesero_id' in data:
                orden.mesero_id = data['mesero_id']
            if 'metodo_pago' in data:
                orden.metodo_pago = data['metodo_pago']
            if 'referencia_pago' in data:
                orden.referencia_pago = data['referencia_pago']
            if 'vuelto' in data:
                orden.vuelto = data['vuelto']
            if 'nota' in data:
                orden.nota = data['nota']

            db.session.commit()
            return jsonify({'message': 'Orden actualizada'}), 200

        if request.method == 'DELETE':
            db.session.delete(orden)
            db.session.commit()
            return jsonify({'message': 'Orden eliminada'}), 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#Obtener Orden por Id
@app.route('/ordenes/<int:id>', methods=['GET'])
def get_orden(id):
    try:
        orden = Ordenes.query.get_or_404(id)
        return jsonify({
            'id': orden.id,
            'cliente_id': orden.cliente_id,
            'total': orden.total,
            'mesa': orden.mesa,
            'estado': orden.estado,
            'mesero_id': orden.mesero_id,
            'metodo_pago': orden.metodo_pago,
            'referencia_pago': orden.referencia_pago,
            'vuelto': orden.vuelto,
            'fecha': orden.fecha,
            'nota': orden.nota
        }), 200

    except Exception as e:
        return jsonify({
            'error': str(e)
        })
    
#Obtener Ordenes por Cliente
@app.route('/ordenes/cliente/<int:id>', methods=['GET'])
def get_ordenes_by_cliente(id):
    try:
        ordenes = Ordenes.query.filter_by(cliente_id=id).all()
        return jsonify([{
            'id': orden.id,
            'cliente_id': orden.cliente_id,
            'total': orden.total,   
            'mesa': orden.mesa,
            'estado': orden.estado,
            'mesero_id': orden.mesero_id,
            'metodo_pago': orden.metodo_pago,
            'referencia_pago': orden.referencia_pago,
            'vuelto': orden.vuelto,
            'fecha': orden.fecha,
            'nota': orden.nota
        } for orden in ordenes]), 200

    except Exception as e:
        return jsonify([{
            'error': str(e)
        }])
    
#Obtener Ordenes por Mesa
@app.route('/ordenes/mesa/<int:id>', methods=['GET'])
def get_ordenes_by_mesa(id):
    try:
        ordenes = Ordenes.query.filter_by(mesa=id).all()
        return jsonify([{
            'id': orden.id,
            'cliente_id': orden.cliente_id,
            'total': orden.total,   
            'mesa': orden.mesa,
            'estado': orden.estado,
            'mesero_id': orden.mesero_id,
            'metodo_pago': orden.metodo_pago,
            'referencia_pago': orden.referencia_pago,
            'vuelto': orden.vuelto,
            'fecha': orden.fecha,
            'nota': orden.nota
        } for orden in ordenes]), 200

    except Exception as e:
        return jsonify([{
            'error': str(e)
        }])

#Ordenes Productos
@app.route('/ordenes_productos', methods=['POST'])
def add_producto_to_orden():
    try:
        data = request.get_json()

        # Validate input data
        if 'orden_id' not in data or 'producto_id' not in data or 'cantidad' not in data or 'producto_precio' not in data:
            return jsonify({'error': 'Faltan datos requeridos'}), 400

        nueva_relacion = OrdenesProductos(
            orden_id=data['orden_id'],
            producto_id=data['producto_id'],
            cantidad=data['cantidad'],
            producto_precio=data['producto_precio'],
            orden_producto_total= data['orden_producto_total']
        )

        db.session.add(nueva_relacion)
        db.session.commit()
        return jsonify({'message': 'Producto añadido a la orden'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/ordenes_productos/<int:orden_id>/<int:producto_id>', methods=['DELETE'])
def remove_producto_from_orden(orden_id, producto_id):
    try:
        relacion = OrdenesProductos.query.filter_by(
            orden_id=orden_id, producto_id=producto_id).first_or_404()
        db.session.delete(relacion)
        db.session.commit()
        return jsonify({'message': 'Producto eliminado de la orden'}), 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Additional route to get all products in an order
@app.route('/ordenes_productos/<int:orden_id>', methods=['GET'])
def get_productos_in_orden(orden_id):
    try:
        productos = OrdenesProductos.query.filter_by(orden_id=orden_id).all()
        return jsonify([{
            'producto_id': p.producto_id,
            'cantidad': p.cantidad,
            'producto_precio': str(p.producto_precio),
            'producto_total': str(p.orden_producto_total)  # Use the correct field
        } for p in productos]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Additional route to update a product in an order
@app.route('/ordenes_productos/<int:orden_id>/<int:producto_id>', methods=['PUT'])
def update_producto_in_orden(orden_id, producto_id):
    try:
        data = request.get_json()
        if 'cantidad' not in data:
            return jsonify({'error': 'Cantidad no proporcionada'}), 400

        relacion = OrdenesProductos.query.filter_by(
            orden_id=orden_id, producto_id=producto_id).first()

        if not relacion:
            return jsonify({'error': 'Relación no encontrada'}), 404

        relacion.cantidad = data['cantidad']
        relacion.orden_producto_total = relacion.producto_precio * relacion.cantidad

        db.session.commit()
        return jsonify({'message': 'Producto actualizado en la orden'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar producto: {str(e)}'}), 500


# Additional route to get all
@app.route('/ordenes_productos', methods=['GET'])
def get_all_ordenes_productos():
    try:
        relaciones = OrdenesProductos.query.all()
        return jsonify([{
            'orden_id': r.orden_id,
            'producto_id': r.producto_id,
            'orden_producto_total': str(r.orden_producto_total)
        } for r in relaciones]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Sesion
@app.route('/sesiones', methods=['GET', 'POST'])
def manage_sesiones():
    try:
        if request.method == 'GET':
            sesiones = Sesion.query.all()
            return jsonify([{'id': s.id, 'estado': s.estado, 'fecha': s.fecha} for s in sesiones]), 200

        if request.method == 'POST':
            data = request.get_json()
            nueva_sesion = Sesion(estado=data['estado'])
            db.session.add(nueva_sesion)
            db.session.commit()
            return jsonify({'message': 'Sesión creada', 'id': nueva_sesion.id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sesiones/<int:id>', methods=['PUT', 'DELETE'])
def manage_sesion(id):
    try:
        sesion = Sesion.query.get_or_404(id)

        if request.method == 'PUT':
            data = request.get_json()
            sesion.estado = data['estado']
            db.session.commit()
            return jsonify({'message': 'Sesión actualizada'}), 200

        if request.method == 'DELETE':
            db.session.delete(sesion)
            db.session.commit()
            return jsonify({'message': 'Sesión eliminada'}), 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
#Sesion por id
@app.route('/sesiones/<int:id>', methods=['GET'])
def get_sesion(id):
    try:
        sesion = Sesion.query.get_or_404(id)
        return jsonify({'id': sesion.id, 'estado': sesion.estado, 'fecha': sesion.fecha}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Sesion Ordenes
@app.route('/sesion_ordenes', methods=['POST'])
def add_orden_to_sesion():
    try:
        data = request.get_json()
        nueva_relacion = SesionOrdenes(
            sesion_id=data['sesion_id'],
            orden_id=data['orden_id']
        )
        db.session.add(nueva_relacion)
        db.session.commit()
        return jsonify({'message': 'Orden añadida a la sesión'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sesion_ordenes/<int:sesion_id>/<int:orden_id>', methods=['DELETE'])
def remove_orden_from_sesion(sesion_id, orden_id):
    try:
        relacion = SesionOrdenes.query.filter_by(
            sesion_id=sesion_id, orden_id=orden_id).first_or_404()
        db.session.delete(relacion)
        db.session.commit()
        return jsonify({'message': 'Orden eliminada de la sesión'}), 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
#Todas las ordenes de una sesion por el id
@app.route('/sesion_ordenes/<int:sesion_id>', methods=['GET'])
def get_ordenes_by_sesion(sesion_id):
    try:
        relaciones = SesionOrdenes.query.filter_by(sesion_id=sesion_id).all()    
        return jsonify([{
            'orden_id': relacion.orden_id,
            'sesion_id': relacion.sesion_id
        } for relacion in relaciones]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Valoraciones
@app.route('/valoraciones', methods=['GET', 'POST'])
def manage_valoraciones():
    try:
        if request.method == 'GET':
            valoraciones = Valoraciones.query.all()
            return jsonify([{
                'id': v.id,
                'descripcion': v.descripcion,
                'calificacion': v.calificacion,
                'cliente_id': v.cliente_id
            } for v in valoraciones]), 200

        if request.method == 'POST':
            data = request.get_json()
            nueva_valoracion = Valoraciones(
                descripcion=data.get('descripcion'),
                calificacion=data['calificacion'],
                cliente_id=data['cliente_id']
            )
            db.session.add(nueva_valoracion)
            db.session.commit()
            return jsonify({'message': 'Valoración creada', 'id': nueva_valoracion.id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/valoraciones/<int:id>', methods=['PUT', 'DELETE'])
def manage_valoracion(id):
    try:
        valoracion = Valoraciones.query.get_or_404(id)

        if request.method == 'PUT':
            data = request.get_json()
            valoracion.descripcion = data.get('descripcion')
            valoracion.calificacion = data['calificacion']
            valoracion.cliente_id = data['cliente_id']
            db.session.commit()
            return jsonify({'message': 'Valoración actualizada'}), 200

        if request.method == 'DELETE':
            db.session.delete(valoracion)
            db.session.commit()
            return jsonify({'message': 'Valoración eliminada'}), 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Main
if __name__ == "__main__":
    with app.app_context():  # Crear el contexto de la aplicación
        db.create_all()  # Crear las tablas en la base de datos
    app.run(host='192.168.68.111', port=5000, debug=True)
