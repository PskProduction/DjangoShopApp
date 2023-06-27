"""
В этом модуле лежат различные наборы представлений.

Разные view интернет-магазина: по товарам, заказам и т.д.
"""
import logging
import json
from timeit import default_timer
from csv import DictWriter

from django.contrib.auth.models import Group, User
from django.contrib.syndication.views import Feed
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.core.cache import cache

from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.request import Request
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .common import save_csv_products
from .models import Product, Order, ProductImage
from .forms import ProductForm, OrderForm, GroupForm
from .serializers import ProductSerializer, OrderSerializer

log = logging.getLogger(__name__)


class UserOrdersListView(LoginRequiredMixin, ListView):
    template_name = 'shopapp/user-orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        self.owner = user
        return Order.objects.filter(user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.owner
        print(context)
        return context


class UserOrdersExportView(View):
    def get(self, request: HttpRequest, user_id) -> JsonResponse:
        cache_key = f'user_orders_data_export_{user_id}'
        orders_data = cache.get(cache_key)
        if orders_data is None:
            user = get_object_or_404(User, id=user_id)
            orders = Order.objects.filter(user=user).order_by('pk')
            orders_data = [
                {
                    'id': order.id,
                    'delivery_address': order.delivery_address,
                    'promocode': order.promocode,
                    'user_id': order.user_id,
                    'products_id': [product.id for product in order.products.all()],
                }
                for order in orders
            ]
            cache.set(cache_key, orders_data, 300)
        return JsonResponse({'orders': orders_data})


@extend_schema(description='Product views CRUD')
class ProductViewSet(ModelViewSet):
    """
    Набор представлений для действий над Product
    Полный CRUD для сущностей товара
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields = ['name', 'description']
    filterset_fields = [
        'name',
        'description',
        'price',
        'discount',
        'archived',
    ]
    ordering_fields = [
        'name',
        'price',
        'discount',
    ]

    @method_decorator(cache_page(60 * 2))
    def list(self, request, *args, **kwargs):
        # print('Hello products list')
        return super().list(request, *args, **kwargs)

    @action(methods=['get'], detail=False)
    def download_csv(self, request: Request):
        response = HttpResponse(content_type='text/csv')
        filename = 'products-export.csv'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        queryset = self.filter_queryset(self.get_queryset())
        fields = [
            'name',
            'description',
            'price',
            'discount',
            'archived',
        ]
        queryset = queryset.only(*fields)
        writer = DictWriter(response, fieldnames=fields)
        writer.writeheader()

        for product in queryset:
            writer.writerow({
                field: getattr(product, field)
                for field in fields
            })

        return response

    @action(
        detail=False,
        methods=['post'],
        parser_classes=[MultiPartParser],
    )
    def upload_csv(self, request: Request):
        products = save_csv_products(
            request.FILES['file'].file,
            encoding=request.encoding,
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Get one Product by ID',
        description='Retrieves product, returns 404 if not found',
        responses={
            '200': ProductSerializer,
            '404': OpenApiResponse(description='Empty response, Product by ID not found')
        }
    )
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
    ]
    filterset_fields = [
        'delivery_address',
        'products',
        'created_at',
        'promocode',
        'user_id',
    ]
    ordering_fields = [
        'delivery_address',
        'products',
        'created_at',
    ]


class ShopIndexView(View):
    # @method_decorator(cache_page(60 * 2))
    def get(self, request: HttpResponse, *args, **kwargs) -> HttpResponse:
        products = [
            ('Laptop', 1999),
            ('Desktop', 2999),
            ('Smartphone', 999)
        ]
        context = {
            'time_running': default_timer(),
            'products': products,
            'items': 2,
        }
        log.debug('Products for shop index: %s', products)
        log.info('Rendering shop index')
        # print('shop index context', context)
        return render(request, 'shopapp/shop-index.html', context=context)


class GroupsListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            'form': GroupForm(),
            'groups': Group.objects.prefetch_related('permissions').all(),
        }
        return render(request, 'shopapp/groups-list.html', context=context)

    def post(self, request: HttpRequest):
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect(request.path)


class ProductDetailsView(DetailView):
    template_name = 'shopapp/products-details.html'
    # model = Product
    queryset = Product.objects.prefetch_related('images')
    context_object_name = 'product'


class ProductsListView(ListView):
    template_name = 'shopapp/products-list.html'
    # model = Product
    context_object_name = 'products'
    queryset = Product.objects.filter(archived=False)


class ProductCreateView(UserPassesTestMixin, CreateView):
    def test_func(self):
        # return self.request.user.groups.filter(name='secret-group').exists()
        # return self.request.user.is_superuser
        return self.request.user.has_perm('shopapp.add_product')

    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('shopapp:products_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProductUpdateView(UserPassesTestMixin, UpdateView):
    def test_func(self):
        return self.request.user.has_perm('shopapp.change_product') \
            and self.request.user == self.get_object().created_by

    model = Product
    form_class = ProductForm
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse('shopapp:products_details',
                       kwargs={'pk': self.object.pk},
                       )

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in form.files.getlist('images'):
            ProductImage.objects.create(
                product=self.object,
                image=image,
            )
        return response


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy('shopapp:products_list')

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)


class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        cache_key = 'products_data_export'
        products_data = cache.get(cache_key)
        if products_data is None:
            products = Product.objects.order_by('pk').all()
            products_data = [
                {
                    'pk': product.pk,
                    'name': product.name,
                    'price': product.price,
                    'archived': product.archived,
                    'created_by': product.created_by.id
                }
                for product in products
            ]
        cache.set(cache_key, products_data, 300)
        return JsonResponse({'products': products_data})


class LatestProductsFeed(Feed):
    title = 'Latest Products'
    description = 'Updates on changes and additions of new products'
    link = reverse_lazy('shopapp:products_list')

    def items(self):
        return Product.objects.order_by('-created_ad')[:10]

    def item_title(self, item: Product):
        return item.name

    def item_description(self, item: Product):
        return item.description


# def create_product(request: HttpRequest):
#     if request.method == 'POST':
#         form = ProductForm(request.POST)
#         if form.is_valid():
#             # name = form.cleaned_data['name']
#             # price = form.cleaned_data['price']
#             # Product.objects.create(** form.cleaned_data)
#             form.save()
#             url = reverse('shopapp:products_list')
#             return redirect(url)
#     else:
#         form = ProductForm()
#     context = {
#         'form': form,
#     }
#     return render(request, 'shopapp/product_form.html', context=context)


class OrdersListView(LoginRequiredMixin, ListView):
    queryset = (
        Order.objects
        .select_related('user')
        .prefetch_related('products')
    )


class OrdersDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'shopapp.view_order'
    queryset = (
        Order.objects
        .select_related('user')
        .prefetch_related('products')
    )


class OrderCreateView(CreateView):
    model = Order
    fields = 'user', 'products', 'promocode', 'delivery_address'
    success_url = reverse_lazy('shopapp:orders_list')


class OrderUpdateView(UpdateView):
    model = Order
    fields = 'user', 'products', 'promocode', 'delivery_address'
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse('shopapp:order_details',
                       kwargs={'pk': self.object.pk},
                       )


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy('shopapp:orders_list')


class OrdersDataExportView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponse('У вас недостаточно прав')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> JsonResponse:
        orders = Order.objects.all()
        orders_data = [
            {
                'id': order.id,
                'delivery_address': order.delivery_address,
                'promocode': order.promocode,
                'user_id': order.user_id,
                'products_id': [product.id for product in order.products.all()],
            }
            for order in orders
        ]
        return JsonResponse({'orders': orders_data})
