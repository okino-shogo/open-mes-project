from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class DataImportView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'master/data_import.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'データ投入'
        return context
