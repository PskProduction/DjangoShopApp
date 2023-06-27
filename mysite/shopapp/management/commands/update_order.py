from django.core.management import BaseCommand
from shopapp.models import Product, Order


class Command(BaseCommand):
    def handle(self, *args, **options):
        order = Order.objects.first()
        if not order:
            return self.stdout.write("No order found")

        product = Product.objects.all()

        for product in product:
            order.products.add(product)

        order.save()
        self.stdout.write(self.style.SUCCESS(f"successfully added products {order.products.all()} to order {order}"))
