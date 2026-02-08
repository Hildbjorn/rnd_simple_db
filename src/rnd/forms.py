from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Contract, ContractType


class ContractForm(forms.ModelForm):
    """Форма для контракта."""
    
    class Meta:
        model = Contract
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'main_contract': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            if self.instance.type and not self.instance.type.is_supplementary:
                self.initial['main_contract'] = self.instance
        else:
            self.fields['main_contract'].required = False
            self.fields['main_contract'].widget = forms.HiddenInput()
            
        if self.instance and self.instance.pk:
            if self.instance.type and self.instance.type.is_supplementary:
                self.fields['type'].queryset = ContractType.objects.filter(is_supplementary=True)
            else:
                self.fields['type'].queryset = ContractType.objects.filter(is_supplementary=False)