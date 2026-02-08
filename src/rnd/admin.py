"""
Административный интерфейс для системы управления контрактами и НИОКР.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import (
    Contract, ContractType, RnD, RnDTask, RnDType, TechnicalSpecification
)


class RnDTaskInline(admin.TabularInline):
    """Inline для отображения задач технического задания."""
    model = RnDTask
    extra = 0
    min_num = 1
    ordering = ['order']
    fields = ['order', 'description', 'is_completed']
    verbose_name = _('Задача')
    verbose_name_plural = _('Задачи')


@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    """Административный интерфейс для типов контрактов."""
    
    list_display = ('short_name', 'name', 'contracts_count')
    search_fields = ('name', 'short_name')
    list_display_links = ('short_name', 'name')
    
    def contracts_count(self, obj):
        """Количество контрактов данного типа."""
        return obj.contracts.count()
    contracts_count.short_description = _('Количество контрактов')


@admin.register(RnDType)
class RnDTypeAdmin(admin.ModelAdmin):
    """Административный интерфейс для типов НИОКР."""
    
    list_display = ('short_name', 'name', 'tech_specs_count')
    search_fields = ('name', 'short_name')
    list_display_links = ('short_name', 'name')
    
    def tech_specs_count(self, obj):
        """Количество технических заданий данного типа."""
        return obj.technical_specifications.count()
    tech_specs_count.short_description = _('Количество ТЗ')


class TechnicalSpecificationInline(admin.TabularInline):
    """Inline для отображения технических заданий контракта."""
    model = TechnicalSpecification
    extra = 0
    fields = ['type', 'code', 'title', 'is_active', 'created_at']
    readonly_fields = ['created_at']
    show_change_link = True
    verbose_name = _('Техническое задание')
    verbose_name_plural = _('Технические задания')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """Административный интерфейс для контрактов."""
    
    list_display = ('number', 'type', 'created_at', 'rnd_link', 'tech_specs_count')
    list_filter = ('type', 'created_at')
    search_fields = ('number',)
    list_select_related = ('type',)
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('type', 'number')
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_inlines(self, request, obj):
        """
        Возвращаем inline только для существующих объектов.
        """
        if obj:  # obj существует при редактировании
            return [TechnicalSpecificationInline]
        return []  # Пустой список для создания нового
    
    def rnd_link(self, obj):
        """Ссылка на связанный НИОКР."""
        if hasattr(obj, 'rnd'):
            url = reverse('admin:rnd_rnd_change', args=[obj.rnd.id])
            return format_html(
                '<a href="{}">Перейти к НИОКР</a>',
                url
            )
        return "-"
    rnd_link.short_description = _('НИОКР')
    
    def tech_specs_count(self, obj):
        """Количество технических заданий."""
        count = obj.technical_specifications.count()
        url = reverse('admin:rnd_technicalspecification_changelist') + f'?contract__id__exact={obj.id}'
        return format_html(
            '<a href="{}">{}</a>',
            url, count
        )
    tech_specs_count.short_description = _('Технические задания')


@admin.register(TechnicalSpecification)
class TechnicalSpecificationAdmin(admin.ModelAdmin):
    """Административный интерфейс для технических заданий."""
    
    list_display = ('code', 'title', 'contract', 'type', 'is_active', 'created_at')
    list_filter = ('type', 'is_active', 'contract__type')
    search_fields = ('code', 'title', 'purpose', 'contract__number')
    list_select_related = ('contract', 'type')
    inlines = [RnDTaskInline]
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('contract', 'type', 'code', 'title')
        }),
        (_('Содержание'), {
            'fields': ('purpose',)
        }),
        (_('Версионность'), {
            'fields': ('is_active', 'previous_version')
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related(
            'contract', 'type', 'previous_version'
        )


@admin.register(RnD)
class RnDAdmin(admin.ModelAdmin):
    """Административный интерфейс для НИОКР."""
    
    list_display = (
        'contract_number',
        'code',
        'title',
        'type_display',
        'status_display',
        'created_at'
    )
    
    list_filter = ('status', 'technical_specification__type', 'technical_specification__contract__type')
    search_fields = (
        'technical_specification__contract__number',
        'technical_specification__code',
        'technical_specification__title'
    )
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('technical_specification', 'status')
        }),
        (_('Связанные объекты'), {
            'fields': ('contract_info', 'tech_spec_info'),
            'classes': ('collapse',)
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'contract_info',
        'tech_spec_info',
        'created_at',
        'updated_at'
    )
    
    def get_queryset(self, request):
        """Оптимизация запросов."""
        return super().get_queryset(request).select_related(
            'technical_specification',
            'technical_specification__contract',
            'technical_specification__contract__type',
            'technical_specification__type'
        )
    
    def contract_number(self, obj):
        """Номер контракта через ТЗ."""
        return obj.technical_specification.contract.number
    contract_number.short_description = _('Номер контракта')
    contract_number.admin_order_field = 'technical_specification__contract__number'
    
    def code(self, obj):
        """Шифр работы."""
        return obj.technical_specification.code
    code.short_description = _('Шифр работы')
    code.admin_order_field = 'technical_specification__code'
    
    def title(self, obj):
        """Тема работы."""
        return obj.technical_specification.title
    title.short_description = _('Тема работы')
    title.admin_order_field = 'technical_specification__title'
    
    def type_display(self, obj):
        """Тип работ."""
        return obj.technical_specification.type.short_name
    type_display.short_description = _('Тип работ')
    type_display.admin_order_field = 'technical_specification__type__short_name'
    
    def status_display(self, obj):
        """Отображение статуса с цветом."""
        status_colors = {
            'draft': 'gray',
            'in_progress': 'orange',
            'completed': 'green',
            'cancelled': 'red',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = _('Статус')
    
    def contract_info(self, obj):
        """Информация о контракте через ТЗ."""
        contract = obj.technical_specification.contract
        url = reverse('admin:rnd_contract_change', args=[contract.id])
        
        return format_html(
            '''
            <div style="padding: 10px; background: #f8f9fa; border-radius: 4px;">
                <strong>Контракт:</strong> {}<br>
                <strong>Тип:</strong> {}<br>
                <a href="{}" class="button">Редактировать контракт</a>
            </div>
            ''',
            contract.number,
            contract.type.short_name if contract.type else "-",
            url
        )
    contract_info.short_description = _('Информация о контракте')
    
    def tech_spec_info(self, obj):
        """Информация о техническом задании."""
        tech_spec = obj.technical_specification
        url = reverse('admin:rnd_technicalspecification_change', args=[tech_spec.id])
        
        return format_html(
            '''
            <div style="padding: 10px; background: #f8f9fa; border-radius: 4px;">
                <strong>Техническое задание:</strong><br>
                <strong>Шифр:</strong> {}<br>
                <strong>Тема:</strong> {}<br>
                <strong>Тип работ:</strong> {}<br>
                <strong>Статус:</strong> {}<br>
                <a href="{}" class="button">Редактировать ТЗ</a>
            </div>
            ''',
            tech_spec.code,
            tech_spec.title,
            tech_spec.type.short_name if tech_spec.type else "-",
            "Активно" if tech_spec.is_active else "Неактивно",
            url
        )
    tech_spec_info.short_description = _('Информация о ТЗ')


@admin.register(RnDTask)
class RnDTaskAdmin(admin.ModelAdmin):
    """Административный интерфейс для задач НИОКР."""
    
    list_display = (
        'order',
        'short_description',
        'technical_specification',
        'is_completed',
        'created_at'
    )
    
    list_filter = ('is_completed', 'technical_specification__contract')
    search_fields = ('description', 'technical_specification__code')
    list_select_related = ('technical_specification',)
    
    def short_description(self, obj):
        """Короткое описание задачи."""
        return obj.description[:100] + "..." if len(obj.description) > 100 else obj.description
    short_description.short_description = _('Описание')