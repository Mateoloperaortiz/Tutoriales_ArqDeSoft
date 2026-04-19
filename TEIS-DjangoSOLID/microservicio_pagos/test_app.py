import unittest

from app import app


class FlaskCompraAPITestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_post_compra_exitosa(self):
        response = self.client.post(
            "/api/v2/comprar",
            json={"producto_id": 7, "cantidad": 3},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "mensaje": "Compra procesada exitosamente por el Microservicio Flask",
                "producto_id": 7,
                "cantidad": 3,
                "status": "Aprobado",
            },
        )

    def test_post_compra_asigna_cantidad_por_defecto(self):
        response = self.client.post("/api/v2/comprar", json={"producto_id": 9})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["cantidad"], 1)

    def test_post_compra_rechaza_falta_de_producto(self):
        response = self.client.post("/api/v2/comprar", json={"cantidad": 1})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "Falta el ID del producto"})

    def test_post_compra_acepta_ruta_con_slash_final(self):
        response = self.client.post("/api/v2/comprar/", json={"producto_id": 5})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["producto_id"], 5)


if __name__ == "__main__":
    unittest.main()
