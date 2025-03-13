from django.views import generic

class TopView(generic.TemplateView):
    template_name = 'top.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
