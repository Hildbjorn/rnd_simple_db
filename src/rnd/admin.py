from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Contract, ContractType, RnD, RnDTask, RnDType, TechnicalSpecification


class RnDTaskInline(admin.TabularInline):
    """
    Inline для задач технического задания.
    """
    model = RnDTask
    extra = 1
    ordering = ['order']
    verbose_name = "Задача работы"
    verbose_name_plural = "Задачи работы"


@admin.register(TechnicalSpecification)
class TechnicalSpecificationAdmin(admin.ModelAdmin):
    model = TechnicalSpecification
    
    list_display = ('type', 'code', 'title', 'contract', 'is_active')
    list_filter = ('type', 'contract', 'is_active')
    search_fields = ('code', 'title', 'purpose', 'contract__number')
    inlines = [RnDTaskInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('contract', 'type', 'code', 'title')
        }),
        ('Цель работы', {
            'fields': ('purpose',)
        }),
        ('Версионность', {
            'fields': ('is_active', 'previous_version')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RnD)
class RnDAdmin(admin.ModelAdmin):
    """
    Основная админка для НИОКР.
    """
    model = RnD
    
    # Поля для отображения в форме редактирования НИОКР
    fields = ('contract', 'get_contract_info', 'get_tech_spec_info')
    readonly_fields = ('get_contract_info', 'get_tech_spec_info')
    
    # Настраиваем отображение списка НИОКР
    list_display = ('get_rnd_type', 'get_rnd_code', 'get_rnd_title', 'get_contract_number', )
    list_display_links = ('get_rnd_type', 'get_rnd_code', 'get_rnd_title', 'get_contract_number')
    list_filter = ('contract__type', 'contract__technical_specifications__type')
    search_fields = ('contract__number', 
                     'contract__technical_specifications__code', 
                     'contract__technical_specifications__title',
                     'contract__technical_specifications__purpose')
    
    def get_contract_info(self, obj):
        """Отображает информацию о контракте с ссылкой на редактирование."""
        if obj.contract:
            url = reverse('admin:rnd_contract_change', args=[obj.contract.id])
            return format_html(
                '<strong>Контракт:</strong> {}<br>'
                '<strong>Тип:</strong> {}<br>'
                '<a href="{}" style="margin-top: 12px; display: inline-block; padding: 6px 15px; background: #4CAF50; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; font-size: 14px;">✎ Редактировать контракт</a><br>',
                obj.contract.number,
                obj.contract.type.name if obj.contract.type else "Не указан",
                url
            )
        return "Контракт не выбран"
    get_contract_info.short_description = 'Информация о контракте'
    
    def get_tech_spec_info(self, obj):
        """Отображает информацию о технических заданиях."""
        if obj.contract:
            tech_specs = obj.contract.technical_specifications.all()
            if tech_specs.exists():
                html = '<strong>Техническое задание:</strong><br>'
                for spec in tech_specs:
                    url = reverse('admin:rnd_technicalspecification_change', args=[spec.id])
                    status = "✓ АКТИВНО" if spec.is_active else "✗ НЕАКТИВНО"
                    html += format_html(
                        '- {} {}: {}<br>'
                        '<a href="{}" style="margin-top: 12px; display: inline-block; padding: 6px 15px; background: #4CAF50; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; font-size: 14px;">✎ Редактировать ТЗ</a><br>',
                        status, spec.code, spec.title, url
                    )
                return format_html(html)
        return "Технические задания не найдены"
    get_tech_spec_info.short_description = 'Техническое задание'
    
    def get_contract_number(self, obj):
        if obj.contract:
            return obj.contract.number
        return "-"
    get_contract_number.short_description = Contract._meta.get_field('number').verbose_name
    get_contract_number.admin_order_field = 'contract__number'
    
    def get_rnd_type(self, obj):
        active_spec = obj.get_active_technical_specification()
        if active_spec and active_spec.type:
            return active_spec.type.name
        return "-"
    get_rnd_type.short_description = RnDType._meta.verbose_name
    get_rnd_type.admin_order_field = 'contract__technical_specifications__type__name'
    
    def get_rnd_code(self, obj):
        active_spec = obj.get_active_technical_specification()
        if active_spec and active_spec.code:
            return active_spec.code
        return "-"
    get_rnd_code.short_description = TechnicalSpecification._meta.get_field('code').verbose_name
    get_rnd_code.admin_order_field = 'contract__technical_specifications__code'
    
    def get_rnd_title(self, obj):
        active_spec = obj.get_active_technical_specification()
        if active_spec and active_spec.title:
            return active_spec.title
        return "-"
    get_rnd_title.short_description = TechnicalSpecification._meta.get_field('title').verbose_name
    get_rnd_title.admin_order_field = 'contract__technical_specifications__title'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Настраиваем виджеты для ForeignKey полей."""
        if db_field.name == "contract":
            # Показываем только контракты, не привязанные к другим НИОКР
            kwargs["queryset"] = Contract.objects.filter(rnd_contracts__isnull=True) | Contract.objects.filter(rnd_contracts=request.resolver_match.kwargs.get('object_id'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    model = ContractType
    list_display = ('short_name', 'name', 'description')


@admin.register(RnDType)
class RnDTypeAdmin(admin.ModelAdmin):
    model = RnDType
    list_display = ('name', 'short_name', 'description')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    model = Contract
    list_display = ('number', 'type', 'get_rnd_info', 'get_tech_specs_count')
    list_filter = ('type',)
    search_fields = ('number',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('type', 'number')
        }),
        ('Связанные объекты', {
            'fields': ('get_rnd_info', 'get_tech_specs_info'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('get_rnd_info', 'get_tech_specs_info')
    
    def get_rnd_info(self, obj):
        """Отображает информацию о НИОКР, связанных с этим контрактом."""
        rnds = obj.rnd_contracts.all()
        if rnds.exists():
            html = '<strong>НИОКР:</strong><br>'
            for rnd in rnds:
                url = reverse('admin:rnd_rnd_change', args=[rnd.id])
                html += format_html(
                    '- <a href="{}">НИОКР #{}</a><br>',
                    url, rnd.id
                )
            return format_html(html)
        return "НИОКР не найдены"
    get_rnd_info.short_description = 'Связанные НИОКР'
    
    def get_tech_specs_count(self, obj):
        return obj.technical_specifications.count()
    get_tech_specs_count.short_description = 'Кол-во ТЗ'
    
    def get_tech_specs_info(self, obj):
        """Отображает информацию о технических заданиях."""
        tech_specs = obj.technical_specifications.all()
        if tech_specs.exists():
            html = '<strong>Техническое задание:</strong><br>'
            for spec in tech_specs:
                url = reverse('admin:rnd_technicalspecification_change', args=[spec.id])
                status = "✓ АКТИВНО" if spec.is_active else "✗ НЕАКТИВНО"
                html += format_html(
                    '- {} {}: {}<br>'
                    '<a href="{}" style="margin-top: 12px; display: inline-block; padding: 6px 15px; background: #4CAF50; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; font-size: 14px;">✎ Редактировать ТЗ</a><br>',
                    status, spec.code, spec.title, url
                )
            return format_html(html)
        return "Технические задания не найдены"
    get_tech_specs_info.short_description = 'Техническое задание'