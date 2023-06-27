from csv import DictReader
from io import TextIOWrapper

from django.contrib.auth.models import User

from shopapp.models import Product, Order


def save_csv_products(file, encoding):
    csv_file = TextIOWrapper(
        file,
        encoding=encoding,
    )
    reader = DictReader(csv_file)

    products = []
    for row in reader:
        user_id = int(row['created_by'])
        user = User.objects.get(id=user_id)
        product = Product(
            name=row['name'],
            description=row['description'],
            price=row['price'],
            discount=row['discount'],
            created_by=user,
        )
        products.append(product)

    Product.objects.bulk_create(products)

    return products

def save_csv_orders(file, encoding):
    csv_file = TextIOWrapper(file, encoding=encoding)
    reader = DictReader(csv_file)
    rows = list(reader)

    orders = []
    for row in rows:
        user_id = int(row['user'])
        user = User.objects.get(id=user_id)

        order = Order.objects.create(
            delivery_address=row['delivery_address'],
            promocode=row['promocode'],
            user=user
        )

        product_ids = [int(pid) for pid in row['products'].split(',')]
        products = Product.objects.filter(id__in=product_ids)
        order.products.set(products)

        orders.append(order)

    return orders

