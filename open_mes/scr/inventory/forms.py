from django import forms

class IssueForm(forms.Form):
    sales_order_number = forms.CharField(
        label="受注番号 (またはスキャンデータ)",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': '受注番号を入力またはスキャン', 'autofocus': 'autofocus'})
    )
    quantity_to_ship = forms.IntegerField(
        label="出庫数量",
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': '出庫する数量'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If you need to dynamically update choices or fields, you can do it here.
        # For example, if barcode input should dynamically populate sales_order_selector:
        # self.fields['sales_order_selector'].choices = ...