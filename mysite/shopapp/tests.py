from string import ascii_letters
from random import choices

from django.contrib.auth.models import User, Permission, Group
from django.test import TestCase
from django.urls import reverse

from mysite import settings
from shopapp.models import Product, Order
from shopapp.utils import add_to_numbers


class AddTwoNumbersTestCase(TestCase):
    def test_add_two_numbers(self):
        result = add_to_numbers(2, 3)
        self.assertEqual(result, 5)


class ProductCreateViewTestCase(TestCase):
    def setUp(self) -> None:
        self.product_name = ''.join(choices(ascii_letters, k=10))
        Product.objects.filter(name=self.product_name).delete()
        self.user = User.objects.create_superuser(username='testuser', password='12345')

    def test_create_product(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('shopapp:product_create'),
            {
                'name': self.product_name,
                'price': "123.45",
                'description': "Good Table",
                'discount': "10",
            },
        )
        self.assertRedirects(response, reverse('shopapp:products_list'))
        self.assertTrue(
            Product.objects.filter(name=self.product_name).exists()
        )


class ProductDetailsViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name='Best Product', created_by=self.user)

    def tearDown(self) -> None:
        self.product.delete()
        self.user.delete()

    def test_get_product(self):
        response = self.client.get(
            reverse('shopapp:products_details', kwargs={'pk': self.product.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_product_and_check_content(self):
        response = self.client.get(
            reverse('shopapp:products_details', kwargs={'pk': self.product.pk})
        )
        self.assertContains(response, self.product.name)


class ProductListViewTestCase(TestCase):
    fixtures = [
        'products-fixture.json',
    ]

    def test_products(self):
        response = self.client.get(reverse('shopapp:products_list'))
        self.assertQuerysetEqual(
            qs=Product.objects.filter(archived=False).all(),
            values=(p.pk for p in response.context['products']),
            transform=lambda p: p.pk,
        )
        self.assertTemplateUsed(response, 'shopapp/products-list.html')


class ProductsExportViewTestCase(TestCase):
    fixtures = [
        'users-fixture.json',
        'products-fixture.json'
    ]

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
        )

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_get_products_view(self):
        response = self.client.get(reverse('shopapp:products_export'))
        self.assertEqual(response.status_code, 200)
        products = Product.objects.order_by('pk').all()
        expected_data = [
            {
                'pk': product.pk,
                'name': product.name,
                'price': str(product.price),
                'archived': product.archived,
                'created_by': product.created_by_id,
            }
            for product in products
        ]
        products_data = response.json()
        self.assertEqual(
            products_data['products'],
            expected_data
        )


class OrdersListViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username='test', password='12345')

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_orders_view(self):
        response = self.client.get(reverse('shopapp:orders_list'))
        self.assertContains(response, 'Orders')

    def test_orders_view_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse('shopapp:orders_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(settings.LOGIN_URL), response.url)


class OrderDetailViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username='test', password='12345')
        cls.user.user_permissions.add(Permission.objects.get(codename='view_order'))

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)
        self.order = Order.objects.create(
            user=self.user,
            delivery_address='Test address',
            promocode='TEST'
        )

    def tearDown(self) -> None:
        self.order.delete()

    def test_orders_details_view(self):
        response = self.client.get(reverse('shopapp:order_details', args=[self.order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['order'].delivery_address, self.order.delivery_address)
        self.assertEqual(response.context['order'].promocode, self.order.promocode)
        self.assertEqual(response.context['order'].id, self.order.id)


class OrdersExportViewTestCase(TestCase):
    fixtures = [
        'orders-fixture.json'
    ]

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            is_staff=True
        )
    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_get_orders_view(self):
        response = self.client.get(reverse('shopapp:orders_export'))
        self.assertEqual(response.status_code, 200)
        orders = Order.objects.all()
        expected_data = [
            {
                'id': order.id,
                'delivery_address': order.delivery_address,
                'promocode': order.promocode,
                'user_id': order.user_id,
                'products_id': [product.id for product in order.products.all()],
            }
            for order in orders
        ]
        orders_data = response.json()
        self.assertEqual(
            orders_data['orders'],
            expected_data
        )
