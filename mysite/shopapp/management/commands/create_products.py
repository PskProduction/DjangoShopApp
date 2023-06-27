from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from shopapp.models import Product


class Command(BaseCommand):
    """
    Create products
    """

    def handle(self, *args, **options):
        self.stdout.write('Check user')
        try:
            user = user = User.objects.get(username='admin')
        except ObjectDoesNotExist:
            user = User.objects.create_user(username='admin', password='admin')
        self.stdout.write("Create products")

        products_names = [
            'Laptop',
            'Desktop',
            'Smartphone',
        ]
        for products_name in products_names:
            product, created = Product.objects.get_or_create(name=products_name, created_by=user)
            self.stdout.write(f'create product {product.name}')
        self.stdout.write(self.style.SUCCESS("Products created successfully"))
