from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection
from datasets.models import Dataset
from charts.models import Chart, SavedQuery


class Command(BaseCommand):
    help = "Seed demo data for BI Dashboard application"

    def handle(self, *args, **options):
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user (admin/admin123)"))

        self._create_demo_tables()
        self._create_datasets(admin_user)
        self._create_charts(admin_user)
        self._create_dashboards(admin_user)
        self._create_saved_queries(admin_user)
        self.stdout.write(self.style.SUCCESS("Seed data completed successfully!"))

    def _create_demo_tables(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS demo_categories")
            cursor.execute("DROP TABLE IF EXISTS demo_products")
            cursor.execute("DROP TABLE IF EXISTS demo_orders")

            cursor.execute("""
                CREATE TABLE demo_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE demo_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    price REAL NOT NULL,
                    category_id INTEGER NOT NULL,
                    in_stock INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE demo_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    customer_email TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    total_amount REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            categories = [
                (1, "Electronics", "Electronic devices and accessories"),
                (2, "Clothing", "Apparel and fashion items"),
                (3, "Books", "Books and publications"),
                (4, "Home & Garden", "Home improvement and garden supplies"),
                (5, "Sports", "Sports equipment and gear"),
            ]
            for c in categories:
                cursor.execute(
                    "INSERT INTO demo_categories (id, name, description) VALUES (%s, %s, %s)", c
                )

            products = [
                ("Laptop", "High-performance laptop", 1299.99, 1, 1),
                ("Smartphone", "Latest model smartphone", 899.99, 1, 1),
                ("Headphones", "Wireless noise-canceling", 249.99, 1, 1),
                ("Tablet", "10-inch display tablet", 499.99, 1, 1),
                ("T-Shirt", "Cotton crew neck", 29.99, 2, 1),
                ("Jeans", "Slim fit denim", 79.99, 2, 1),
                ("Jacket", "Waterproof winter jacket", 149.99, 2, 0),
                ("Python Programming", "Learn Python from scratch", 39.99, 3, 1),
                ("Data Science Handbook", "Comprehensive guide", 49.99, 3, 1),
                ("Garden Shovel", "Ergonomic handle", 24.99, 4, 1),
                ("Plant Pot Set", "Set of 3 ceramic pots", 34.99, 4, 1),
                ("Yoga Mat", "Non-slip exercise mat", 19.99, 5, 1),
                ("Running Shoes", "Lightweight running shoes", 89.99, 5, 1),
                ("Dumbbell Set", "Adjustable weights 10kg", 59.99, 5, 1),
            ]
            for p in products:
                cursor.execute(
                    "INSERT INTO demo_products (name, description, price, category_id, in_stock) VALUES (%s, %s, %s, %s, %s)",
                    p,
                )

            orders = [
                ("Alice Johnson", "alice@example.com", "delivered", 1629.97),
                ("Bob Smith", "bob@example.com", "shipped", 899.99),
                ("Carol Davis", "carol@example.com", "processing", 349.97),
                ("Dan Wilson", "dan@example.com", "pending", 1299.99),
                ("Eve Martin", "eve@example.com", "delivered", 109.98),
                ("Frank Lee", "frank@example.com", "cancelled", 79.99),
                ("Grace Kim", "grace@example.com", "delivered", 529.98),
                ("Henry Brown", "henry@example.com", "shipped", 249.99),
                ("Ivy Chen", "ivy@example.com", "processing", 44.98),
                ("Jack Davis", "jack@example.com", "pending", 189.98),
            ]
            for o in orders:
                cursor.execute(
                    "INSERT INTO demo_orders (customer_name, customer_email, status, total_amount) VALUES (%s, %s, %s, %s)",
                    o,
                )

        self.stdout.write(self.style.SUCCESS("Created demo_db tables with seed data"))

    def _create_datasets(self, user):
        datasets_data = [
            {
                "name": "Categories",
                "description": "Product categories",
                "table_name": "demo_categories",
                "columns": [
                    {"name": "id", "type": "integer", "label": "ID"},
                    {"name": "name", "type": "string", "label": "Name"},
                    {"name": "description", "type": "string", "label": "Description"},
                    {"name": "created_at", "type": "datetime", "label": "Created At"},
                    {"name": "updated_at", "type": "datetime", "label": "Updated At"},
                ],
            },
            {
                "name": "Products",
                "description": "Products catalog",
                "table_name": "demo_products",
                "columns": [
                    {"name": "id", "type": "integer", "label": "ID"},
                    {"name": "name", "type": "string", "label": "Name"},
                    {"name": "description", "type": "string", "label": "Description"},
                    {"name": "price", "type": "decimal", "label": "Price"},
                    {"name": "category_id", "type": "integer", "label": "Category ID"},
                    {"name": "in_stock", "type": "boolean", "label": "In Stock"},
                    {"name": "created_at", "type": "datetime", "label": "Created At"},
                    {"name": "updated_at", "type": "datetime", "label": "Updated At"},
                ],
            },
            {
                "name": "Orders",
                "description": "Customer orders",
                "table_name": "demo_orders",
                "columns": [
                    {"name": "id", "type": "integer", "label": "ID"},
                    {"name": "customer_name", "type": "string", "label": "Customer Name"},
                    {"name": "customer_email", "type": "string", "label": "Customer Email"},
                    {"name": "status", "type": "string", "label": "Status"},
                    {"name": "total_amount", "type": "decimal", "label": "Total Amount"},
                    {"name": "created_at", "type": "datetime", "label": "Created At"},
                    {"name": "updated_at", "type": "datetime", "label": "Updated At"},
                ],
            },
        ]

        for data in datasets_data:
            ds, created = Dataset.objects.get_or_create(
                name=data["name"],
                defaults={**data, "row_count": None, "created_by": user},
            )
            if created:
                self.stdout.write(f"  Created dataset: {ds.name}")

    def _create_charts(self, user):
        products_ds = Dataset.objects.get(name="Products")
        orders_ds = Dataset.objects.get(name="Orders")
        categories_ds = Dataset.objects.get(name="Categories")

        charts_data = [
            {
                "name": "Products by Category",
                "description": "Count of products grouped by category",
                "dataset": products_ds,
                "chart_type": "bar",
                "config": {
                    "x_axis": "category_id",
                    "y_axis": "id",
                    "aggregate": "count",
                    "sort": {"column": "id", "direction": "desc"},
                },
            },
            {
                "name": "Order Status Distribution",
                "description": "Pie chart of order statuses",
                "dataset": orders_ds,
                "chart_type": "pie",
                "config": {"x_axis": "status", "y_axis": "id", "aggregate": "count"},
            },
            {
                "name": "Revenue Over Time",
                "description": "Line chart of order totals by date",
                "dataset": orders_ds,
                "chart_type": "line",
                "config": {
                    "x_axis": "created_at",
                    "y_axis": "total_amount",
                    "aggregate": "sum",
                },
            },
            {
                "name": "Categories Overview",
                "description": "Count of categories by name",
                "dataset": categories_ds,
                "chart_type": "bar",
                "config": {"x_axis": "name", "y_axis": "id", "aggregate": "count"},
            },
            {
                "name": "Product Price Distribution",
                "description": "Scatter chart of product prices",
                "dataset": products_ds,
                "chart_type": "scatter",
                "config": {"x_axis": "id", "y_axis": "price", "aggregate": "none"},
            },
        ]

        for data in charts_data:
            chart, created = Chart.objects.get_or_create(
                name=data["name"],
                defaults={**data, "created_by": user},
            )
            if created:
                self.stdout.write(f"  Created chart: {chart.name}")

    def _create_dashboards(self, user):
        from dashboards.models import Dashboard

        charts = list(Chart.objects.all()[:4])
        if not charts:
            return

        layout = {
            "charts": [
                {"chart_id": charts[0].id, "x": 0, "y": 0, "w": 6, "h": 4},
            ]
        }
        if len(charts) > 1:
            layout["charts"].append({"chart_id": charts[1].id, "x": 6, "y": 0, "w": 6, "h": 4})
        if len(charts) > 2:
            layout["charts"].append({"chart_id": charts[2].id, "x": 0, "y": 4, "w": 6, "h": 4})
        if len(charts) > 3:
            layout["charts"].append({"chart_id": charts[3].id, "x": 6, "y": 4, "w": 6, "h": 4})

        dashboard, created = Dashboard.objects.get_or_create(
            name="Sales Overview",
            defaults={
                "description": "Key sales metrics and charts",
                "layout": layout,
                "created_by": user,
            },
        )
        if created:
            self.stdout.write(f"  Created dashboard: {dashboard.name}")

    def _create_saved_queries(self, user):
        queries = [
            {"name": "All Products", "sql": "SELECT * FROM demo_products LIMIT 20"},
            {"name": "Product Count by Category", "sql": "SELECT category_id, COUNT(*) as count FROM demo_products GROUP BY category_id ORDER BY count DESC"},
            {"name": "Recent Orders", "sql": "SELECT id, customer_name, status, total_amount, created_at FROM demo_orders ORDER BY created_at DESC LIMIT 10"},
            {"name": "Revenue Summary", "sql": "SELECT status, COUNT(*) as order_count, SUM(total_amount) as total_revenue FROM demo_orders GROUP BY status"},
        ]
        for q in queries:
            sq, created = SavedQuery.objects.get_or_create(
                name=q["name"],
                defaults={"sql": q["sql"], "dataset": None, "created_by": user},
            )
            if created:
                self.stdout.write(f"  Created saved query: {sq.name}")
