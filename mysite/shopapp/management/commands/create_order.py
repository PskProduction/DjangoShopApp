from typing import Sequence

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.db import transaction
from shopapp.models import Order, Product


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Check user')
        try:
            user = user = User.objects.get(username='admin')
        except ObjectDoesNotExist:
            user = User.objects.create_user(username='admin', password='admin')

        self.stdout.write('create order with products')
        products: Sequence[Product] = Product.objects.only('id').all()
        order, created = Order.objects.get_or_create(
            delivery_address='ul Ivanova, d 8',
            promocode='promo5',
            user=user,
        )
        for product in products:
            order.products.add(product)
        order.save()
        self.stdout.write(f'Created order {order}')
