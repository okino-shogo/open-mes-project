from django.shortcuts import render, redirect
from django.views import View


class QualityMenuView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'quality/menu.html')

class ProcessInspectionView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'quality/process_inspection.html')

class AcceptanceInspectionView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'quality/acceptance_inspection.html')

class MasterCreationView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'quality/master_creation.html')
