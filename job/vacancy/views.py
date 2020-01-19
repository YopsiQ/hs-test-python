import http

from django.shortcuts import render
from django import views
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.generic import CreateView
from django.http.response import HttpResponse, Http404
from django.shortcuts import redirect

from .models import Resume, Vacancy

# Create your views here.

class MenuView(views.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'vacancy/index.html')


class VacanciesView(views.View):
    def get(self, request, *args, **kwargs):
        return render(
            request,
            'vacancy/items.html',
            context={'items': Vacancy.objects.all()}
        )


class ResumesView(views.View):
    def get(self, request, *args, **kwargs):
        return render(
            request,
            'vacancy/items.html',
            context={'items': Resume.objects.all()}
        )


class LoginMeView(LoginView):
    redirect_authenticated_user = True
    template_name = 'vacancy/login.html'


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = 'login'
    template_name = 'vacancy/signup.html'


class HomeView(views.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'vacancy/home.html')


class CreateVacancyView(views.View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return HttpResponse('', status=http.HTTPStatus.FORBIDDEN)
        Vacancy.objects.create(author=request.user, description=request.POST['description'])
        return redirect('/home')


class CreateResumeView(views.View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse('', status=http.HTTPStatus.FORBIDDEN)
        Resume.objects.create(author=request.user, description=request.POST['description'])
        return redirect('/home')
