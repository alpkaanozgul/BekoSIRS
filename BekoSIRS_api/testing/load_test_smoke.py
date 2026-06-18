"""BekoSIRS Smoke Test — 10 users / 60 seconds (headless)."""
from locust import HttpUser, task, between
import random


class BekoSIRSAdminUser(HttpUser):
    """Simulates an authenticated admin/power user hitting common endpoints."""
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self):
        resp = self.client.post("/api/v1/token/", json={
            "username": "loadtest_admin",
            "password": "LoadAdmin123!",
            "login_type": "web",
        }, name="POST /token (login)")
        if resp.status_code == 200:
            token = resp.json().get("access", "")
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(10)
    def list_products(self):
        self.client.get("/api/v1/products/", headers=self.headers,
                        name="GET /products/")

    @task(5)
    def product_detail(self):
        pid = random.randint(1, 50)
        self.client.get(f"/api/v1/products/{pid}/", headers=self.headers,
                        name="GET /products/{id}/")

    @task(4)
    def search_products(self):
        terms = ["Buzdolabi", "Camasir", "Firin", "TV", "Beko"]
        self.client.get(f"/api/v1/products/?search={random.choice(terms)}",
                        headers=self.headers, name="GET /products/?search=")

    @task(3)
    def list_categories(self):
        self.client.get("/api/v1/categories/", headers=self.headers,
                        name="GET /categories/")

    @task(2)
    def recommendations(self):
        self.client.get("/api/v1/recommendations/", headers=self.headers,
                        name="GET /recommendations/")

    @task(2)
    def notifications(self):
        self.client.get("/api/v1/notifications/", headers=self.headers,
                        name="GET /notifications/")

    @task(1)
    def dashboard_summary(self):
        self.client.get("/api/v1/dashboard/summary/", headers=self.headers,
                        name="GET /dashboard/summary/")
