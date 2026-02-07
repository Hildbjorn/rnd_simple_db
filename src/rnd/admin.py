from django.contrib import admin

from .models import RnD, RnDType

@admin.register(RnDType)
class RnDTypeAdmin(admin.ModelAdmin):
    model = RnDType

@admin.register(RnD)
class RnDAdmin(admin.ModelAdmin):
    model = RnD
