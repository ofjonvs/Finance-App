from django import forms
from .models import Holding, BudgetItem
import calendar
import datetime

class HoldingForm(forms.Form):
    symbol = forms.CharField(
        max_length=5,
        min_length=1,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True}),
    )
    dollars_invested = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        help_text="Total dollars invested in this fund (optional, used for calculations)"
    )
    shares = forms.DecimalField(
        max_digits=15,
        decimal_places=4,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        help_text="Total dollars invested in this fund (optional, used for calculations)"
    )

    def clean(self):
        cleaned_data = super().clean()
        dollars_invested = cleaned_data.get('dollars_invested')
        shares = cleaned_data.get('shares')

        # Validate that exactly one of dollars_invested or shares is provided
        if (dollars_invested is None and shares is None) or (dollars_invested is not None and shares is not None):
            raise forms.ValidationError(
                "Exactly one of 'Dollars Invested' or 'Shares' must be provided, but not both."
            )
        return cleaned_data

class BudgetForm(forms.ModelForm):
    month = forms.ChoiceField(
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)], 
        widget=forms.Select(attrs={'class': 'form-control'}), 
        help_text="Month of the expense",
        initial=datetime.datetime.today().month)
    class Meta:
        model = BudgetItem
        fields = ['item', 'category', 'subcategory', 'amount', 'month']
        widgets = {
            'item': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # 'month': forms.Select(attrs={'class': 'form-control'}),
        }