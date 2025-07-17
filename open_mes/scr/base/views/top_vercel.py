from django.views import generic
from django.http import HttpResponse

class TopView(generic.TemplateView):
    """
    Vercel demo version of TopView - simplified without database operations
    """
    template_name = 'top.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['demo_mode'] = True
        context['user_authenticated'] = False  # For demo purposes
        return context