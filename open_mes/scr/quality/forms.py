from django import forms
from django.forms import inlineformset_factory
from .models import InspectionItem, MeasurementDetail

class InspectionItemForm(forms.ModelForm):
    class Meta:
        model = InspectionItem
        fields = [
            'code', 'name', 'description', 
            'inspection_type', 'target_object_type', 
            'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inspection_type': forms.Select(attrs={'class': 'form-control'}),
            'target_object_type': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MeasurementDetailForm(forms.ModelForm):
    class Meta:
        model = MeasurementDetail
        fields = [
            'name', 'measurement_type', 
            'specification_nominal', 'specification_upper_limit', 
            'specification_lower_limit', 'specification_unit',
            'expected_qualitative_result', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'measurement_type': forms.Select(attrs={'class': 'form-control form-control-sm measurement-type-select'}),
            'specification_nominal': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'specification_upper_limit': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'specification_lower_limit': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'specification_unit': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'expected_qualitative_result': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'order': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }

MeasurementDetailFormSet = inlineformset_factory(
    InspectionItem, MeasurementDetail, form=MeasurementDetailForm,
    extra=1, can_delete=True, can_order=False # `can_order=True` にするとDjangoが自動で順序フィールドを扱うが、今回は手動で'order'フィールドを設けた
)