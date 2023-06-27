from random import random

from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, ListView, DetailView
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.decorators.cache import cache_page

from .models import Profile
from .forms import ProfileForm


class HelloView(View):
    welcome_message = _('welcome hello world!')

    def get(self, request: HttpRequest) -> HttpResponse:
        items_str = request.GET.get('items') or 0
        items = int(items_str)
        products_line = ngettext(
            'one product',
            '{count} products',
            items,
        )
        products_line = products_line.format(count=items)
        return HttpResponse(
            f'<h1>{self.welcome_message}</h1>'
            f'\n<h2>{products_line}</h2>'
        )


class AboutMeView(View):
    template_name = 'myauth/about-me.html'

    def get(self, request, *args, **kwargs):
        profile = Profile.objects.get(user=request.user)
        form = ProfileForm(instance=profile)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        profile = Profile.objects.get(user=request.user)
        form = ProfileForm(instance=profile, data=request.POST)
        avatar = request.FILES.get('avatar')
        if form.is_valid():
            profile = form.save(commit=False)
            if avatar:
                profile.avatar = avatar
            form.save()
            return redirect('myauth:about-me')
        return render(request, self.template_name, {'form': form})


class UserListView(ListView):
    model = User
    template_name = 'myauth/users.html'
    context_object_name = 'users'


class UserDetailView(View):
    template_name = 'myauth/user-detail.html'

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user:
            profile = Profile.objects.get(user=user)
            form = ProfileForm(instance=profile)
            return render(request, self.template_name, {'form': form, 'user': user})
        else:
            HttpResponseForbidden()

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if request.user.is_staff or request.user == user:
            profile = Profile.objects.get(user=user)
            form = ProfileForm(instance=profile, data=request.POST)
            avatar = request.FILES.get('avatar')
            if form.is_valid():
                profile = form.save(commit=False)
                if avatar:
                    profile.avatar = avatar
                form.save()
                return redirect('myauth:user_detail', pk=pk)
            return render(request, self.template_name, {'form': form, 'user': user})
        else:
            return HttpResponseForbidden()


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'myauth/register.html'
    success_url = reverse_lazy('myauth:about-me')

    def form_valid(self, form):
        response = super().form_valid(form)
        Profile.objects.create(user=self.object)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(
            self.request,
            username=username,
            password=password
        )
        login(request=self.request, user=user)
        return response


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('/admin')

        return render(request, 'myauth/login.html')

    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return redirect('/admin')

    return render(request, 'myauth/login.html', {'error': 'Invalid login credentials'})


def logout_view(request: HttpRequest):
    logout(request)
    return redirect(reverse('myauth:login'))


class MyLogoutView(LogoutView):
    next_page = reverse_lazy('myauth:login')


def set_cookie_view(request: HttpRequest) -> HttpResponse:
    response = HttpResponse('Cookie set')
    response.set_cookie('fizz', 'buzz', max_age=3600)
    return response


@cache_page(60 * 2)
def get_cookie_view(request: HttpRequest) -> HttpResponse:
    value = request.COOKIES.get('fizz', 'default value')
    return HttpResponse(f'Cookie value: {value!r} + {random()}')


@permission_required('myauth.view_profile', raise_exception=True)
def set_session_view(request: HttpRequest) -> HttpResponse:
    request.session['foobar'] = 'spameggs'
    return HttpResponse('Session set!')


@login_required
def get_session_view(request: HttpRequest):
    value = request.session.get('foobar', 'default')
    return HttpResponse(f'Session value: {value!r}')


class FooBarView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({'spam': 'eggs', 'foo': 'bar', })
