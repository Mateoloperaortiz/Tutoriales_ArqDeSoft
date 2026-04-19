from flask import Flask, jsonify, request

app = Flask(__name__)
app.url_map.strict_slashes = False


@app.post("/api/v2/comprar")
def realizar_compra():
    data = request.get_json(silent=True) or {}
    producto_id = data.get("producto_id")
    cantidad = data.get("cantidad", 1)

    if not producto_id:
        return jsonify({"error": "Falta el ID del producto"}), 400

    return (
        jsonify(
            {
                "mensaje": "Compra procesada exitosamente por el Microservicio Flask",
                "producto_id": producto_id,
                "cantidad": cantidad,
                "status": "Aprobado",
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
