from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

# Create your views here.

class UserSettingsView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'users/settings.html'
    # login_url = reverse_lazy('users_login') # settings.LOGIN_URL is used by default

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ユーザー設定'
        return context
