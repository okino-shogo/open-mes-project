from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse
from django.db import transaction # For atomic transactions with formsets
from django.db.models import ProtectedError
from django.forms.models import ModelChoiceIteratorValue
from .models import InspectionItem, MeasurementDetail # MeasurementDetail
from .forms import InspectionItemForm, MeasurementDetailFormSet # Import MeasurementDetailFormSet

class QualityMenuView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'quality/menu.html')

class ProcessInspectionView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'quality/process_inspection.html')

class AcceptanceInspectionView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'quality/acceptance_inspection.html')

class InspectionItemMasterView(View):
    template_name = 'quality/master_creation.html'
    # form_class is not directly used by this view for rendering the main page's form anymore
    # as the form is now in a modal loaded via iframe.

    def get(self, request, *args, **kwargs):
        items = InspectionItem.objects.all().order_by('code')
        # The main page doesn't need the form instance directly if it's always in a modal.
        return render(request, self.template_name, {'items': items, 'page_title': '検査項目マスター管理'})


def _serialize_bound_field(bound_field):
    """Helper to convert BoundField data to a JSON-serializable format."""
    current_val = bound_field.value()
    processed_value = current_val.value if isinstance(current_val, ModelChoiceIteratorValue) else current_val

    processed_choices = []
    if hasattr(bound_field.field, 'choices'):
        for choice_val, choice_label in bound_field.field.choices:
            actual_choice_val = choice_val.value if isinstance(choice_val, ModelChoiceIteratorValue) else choice_val
            processed_choices.append((actual_choice_val, str(choice_label))) # Ensure label is string

    return {
        'label': str(bound_field.label), # Ensure label is string
        'html_name': bound_field.html_name,
        'value': processed_value,
        'errors': bound_field.errors, # ErrorList is usually fine
        'widget_type': bound_field.field.widget.__class__.__name__,
        'is_required': bound_field.field.required,
        'choices': processed_choices
    }



def inspection_item_create(request):
    if request.method == 'POST':
        form = InspectionItemForm(request.POST)
        # Initialize formset with POST data, but no instance yet for create
        formset = MeasurementDetailFormSet(request.POST, prefix='measurement_details')

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    inspection_item = form.save()
                    formset.instance = inspection_item # Associate formset with the saved item
                    formset.save()
                return JsonResponse({'success': True, 'message': '検査項目を登録しました。'})
            except Exception as e:
                # Log the exception e
                return JsonResponse({'success': False, 'message': f'保存中にエラーが発生しました: {str(e)}'}, status=500)
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            for i, fs_err in enumerate(formset.errors):
                if fs_err: # fs_err is a dict of errors for that form in the formset
                    for field, error_list in fs_err.items():
                        errors[f'measurement_details-{i}-{field}'] = error_list[0]
            if formset.non_form_errors():
                 errors['formset_non_form_errors'] = formset.non_form_errors()

            return JsonResponse({'success': False, 'errors': errors, 'message': '入力内容を確認してください。'}, status=400)
            
    elif request.method == 'GET':
        # GETリクエスト時には、フォームとフォームセットの構造と初期値をJSONで返す
        form = InspectionItemForm()
        formset = MeasurementDetailFormSet(prefix='measurement_details', instance=InspectionItem())

        form_fields_data = {
            field_name: _serialize_bound_field(form[field_name])
            for field_name in form.fields
        }

        # フォームセットの情報を準備
        formset_data = {
            'prefix': formset.prefix,
            'management_form': {key: formset.management_form[key].value() for key in formset.management_form.fields},
            'forms': [] # 新規作成時は空
        }
        empty_form_fields_data = {
            field_name: _serialize_bound_field(formset.empty_form[field_name])
            for field_name in formset.empty_form.fields
        }

        return JsonResponse({
            'form_data': form_fields_data,
            'formset_data': formset_data,
            'empty_form_fields_data': empty_form_fields_data,
            'page_title': '新規検査項目登録'
        })
    return JsonResponse({'success': False, 'message': '無効なリクエストメソッドです。'}, status=405)


def inspection_item_update(request, pk):
    item = get_object_or_404(InspectionItem, pk=pk)
    if request.method == 'POST':
        form = InspectionItemForm(request.POST, instance=item)
        formset = MeasurementDetailFormSet(request.POST, instance=item, prefix='measurement_details')
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                return JsonResponse({'success': True, 'message': '検査項目を更新しました。'})
            except Exception as e:
                # Log the exception e
                return JsonResponse({'success': False, 'message': f'更新中にエラーが発生しました: {str(e)}'}, status=500)
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            for i, fs_err in enumerate(formset.errors):
                if fs_err:
                    for field, error_list in fs_err.items():
                        errors[f'measurement_details-{i}-{field}'] = error_list[0]
            if formset.non_form_errors():
                 errors['formset_non_form_errors'] = formset.non_form_errors()
            return JsonResponse({'success': False, 'errors': errors, 'message': '入力内容を確認してください。'}, status=400)

    elif request.method == 'GET':
        # GETリクエスト時には、フォームとフォームセットの構造と初期値をJSONで返す
        form = InspectionItemForm(instance=item)
        formset = MeasurementDetailFormSet(instance=item, prefix='measurement_details')

        form_fields_data = {
            field_name: _serialize_bound_field(form[field_name])
            for field_name in form.fields
        }

        formset_data = {
            'prefix': formset.prefix,
            'management_form': {
                key: formset.management_form[key].value() for key in formset.management_form.fields
            },
            'forms': []
        }
        for sub_form in formset.forms:
            serialized_sub_form_fields = {
                field_name: _serialize_bound_field(sub_form[field_name])
                for field_name in sub_form.fields
            }
            formset_data['forms'].append({
                'id': sub_form.instance.pk if sub_form.instance.pk else None,
                'fields': serialized_sub_form_fields,
                'can_delete': bool(sub_form.instance.pk)
            })

        return JsonResponse({
            'form_data': form_fields_data,
            'formset_data': formset_data,
            'empty_form_fields_data': {field_name: _serialize_bound_field(formset.empty_form[field_name]) for field_name in formset.empty_form.fields}, # For adding new rows dynamically
            'page_title': f'検査項目変更: {item.name}'
        })
    return JsonResponse({'success': False, 'message': '無効なリクエストメソッドです。'}, status=405)


def inspection_item_delete(request, pk):
    item = get_object_or_404(InspectionItem, pk=pk)
    if request.method == 'POST':
        try:
            item_code = item.code
            item.delete()
            return JsonResponse({'success': True, 'message': f'検査項目「{item_code}」を削除しました。'})
        except ProtectedError:
            return JsonResponse({
                'success': False,
                'message': f'検査項目「{item.code}」は実績データが関連付けられているため削除できません。'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'削除中にエラーが発生しました: {str(e)}'
            }, status=400)
    return JsonResponse({'success': False, 'message': '無効なリクエストです。'}, status=405)
