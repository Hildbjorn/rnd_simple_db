from django.contrib import admin

from .models import Contract, ContractType, RnD, RnDType

@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    model = ContractType
    
    list_display = ('short_name', 'name', 'description')

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    model = Contract
    
    list_display = ('type','number',)

@admin.register(RnDType)
class RnDTypeAdmin(admin.ModelAdmin):
    model = RnDType
    
    list_display = ('name', 'short_name', 'description')

@admin.register(RnD)
class RnDAdmin(admin.ModelAdmin):
    model = RnD
    
    list_display = ('type', 'code', 'title', 'contract')
