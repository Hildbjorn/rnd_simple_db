"""
Админка для моделей.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django import forms
from django.db.models import Count

from .models import (
    Contract, ContractType, RnD, RnDTask, RnDType, TechnicalSpecification,
    update_all_rnd_statuses_for_contract
)
from .forms import ContractForm


class SupplementaryAgreementInline(admin.TabularInline):
    model = Contract
    fk_name = 'main_contract'
    extra = 0
    max_num = 10
    fields = ['type', 'number', 'name', 'signed_date', 'effective_date', 'status']
    readonly_fields = ['created_at']
    verbose_name = _('Доп. соглашение')
    verbose_name_plural = _('Дополнительные соглашения')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(type__is_supplementary=True)
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj and obj.pk:
            supplementary_types = ContractType.objects.filter(
                is_supplementary=True,
                parent_type=obj.type
            )
            if 'type' in formset.form.base_fields:
                formset.form.base_fields['type'].queryset = supplementary_types
            if 'main_contract' in formset.form.base_fields:
                formset.form.base_fields['main_contract'].initial = obj
                formset.form.base_fields['main_contract'].widget = forms.HiddenInput()
        return formset
    
    def has_add_permission(self, request, obj=None):
        if obj and obj.pk and not obj.type.is_supplementary:
            return True
        return False


class TechnicalSpecificationInline(admin.TabularInline):
    model = TechnicalSpecification
    extra = 0
    max_num = 10
    fields = ['contract_document', 'version', 'document', 'is_active', 'uploaded_at']
    readonly_fields = ['uploaded_at']
    verbose_name = _('ТЗ')
    verbose_name_plural = _('Технические задания')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            allowed_contracts = Contract.objects.filter(
                id=obj.contract.id
            ) | Contract.objects.filter(
                main_contract=obj.contract,
                type__is_supplementary=True
            )
            formset.form.base_fields['contract_document'].queryset = allowed_contracts
        return formset


class RnDTaskInline(admin.TabularInline):
    model = RnDTask
    extra = 0
    max_num = 20
    fields = ['order', 'source_specification', 'description', 'is_completed']
    verbose_name = _('Задача')
    verbose_name_plural = _('Задачи')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            formset.form.base_fields['source_specification'].queryset = \
                TechnicalSpecification.objects.filter(rnd=obj)
        return formset


@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'name', 'is_supplementary_display', 'parent_type_display', 'contracts_count')
    list_filter = ('is_supplementary',)
    search_fields = ('name', 'short_name')
    list_display_links = ('short_name', 'name')
    fieldsets = (
        (None, {'fields': ('name', 'short_name', 'description')}),
        (_('Классификация'), {'fields': ('is_supplementary', 'parent_type')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(contracts_count=Count('contracts'))
    
    def is_supplementary_display(self, obj):
        if obj.is_supplementary:
            return format_html(
                '<span style="color: #666; background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">{}</span>',
                _('Доп. соглашение')
            )
        return format_html(
            '<span style="color: #2196F3; background: #e3f2fd; padding: 2px 6px; border-radius: 3px; font-weight: bold;">{}</span>',
            _('Основной договор')
        )
    is_supplementary_display.short_description = _('Тип')
    
    def parent_type_display(self, obj):
        return obj.parent_type.short_name if obj.parent_type else "-"
    parent_type_display.short_description = _('Родительский тип')
    
    def contracts_count(self, obj):
        return obj.contracts_count
    contracts_count.short_description = _('Документов')
    contracts_count.admin_order_field = 'contracts_count'


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    form = ContractForm
    list_display = (
        'number', 'name', 'type_display', 'signed_date', 'effective_date',
        'status_display', 'is_supplementary_display', 'related_documents_count'
    )
    list_filter = ('type', 'status', ('type__is_supplementary', admin.BooleanFieldListFilter), 'signed_date')
    search_fields = ('number', 'name', 'description')
    list_select_related = ('type', 'main_contract')
    readonly_fields = ('created_at', 'updated_at', 'contract_status_display')
    inlines = [SupplementaryAgreementInline]
    
    fieldsets = (
        (_('Классификация'), {'fields': ('type', 'main_contract')}),
        (_('Основная информация'), {'fields': ('number', 'name', 'description')}),
        (_('Даты и статус'), {'fields': ('signed_date', 'effective_date', 'status')}),
        (_('Документ'), {'fields': ('document',), 'classes': ('collapse',)}),
        (_('Версии'), {'fields': ('previous_version',), 'classes': ('collapse',)}),
        (_('Системная информация'), {'fields': ('contract_status_display', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('type', 'main_contract').prefetch_related('related_documents')
        return qs.annotate(related_docs_count=Count('related_documents'))
    
    def type_display(self, obj):
        return obj.type.short_name
    type_display.short_description = _('Тип')
    type_display.admin_order_field = 'type__short_name'
    
    def is_supplementary_display(self, obj):
        if obj.type.is_supplementary:
            return format_html(
                '<span style="color: #666;">{} к {}</span>',
                _('ДС'),
                obj.main_contract.number if obj.main_contract else '-'
            )
        return format_html(
            '<span style="color: #2196F3; font-weight: bold;">{}</span>',
            _('Основной')
        )
    is_supplementary_display.short_description = _('Вид')
    
    def status_display(self, obj):
        status_colors = {
            'active': '#4caf50',
            'suspended': '#ff9800',
            'completed': '#2196f3',
            'terminated': '#f44336',
        }
        color = status_colors.get(obj.status, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = _('Статус')
    
    def contract_status_display(self, obj):
        if obj.is_main_contract:
            return format_html(
                '<strong>{}:</strong> {}',
                _('Это основной договор'),
                obj.get_status_display()
            )
        else:
            return format_html(
                '<strong>{}:</strong> {}<br><strong>{}:</strong> {}',
                _('Статус этого документа'),
                obj.get_status_display(),
                _('Статус основного договора'),
                obj.contract_status
            )
    contract_status_display.short_description = _('Статусы')
    
    def related_documents_count(self, obj):
        count = obj.related_docs_count if hasattr(obj, 'related_docs_count') else obj.related_documents.count()
        if count > 0 and obj.is_main_contract:
            url = reverse('admin:rnd_contract_changelist') + f'?main_contract__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    related_documents_count.short_description = _('Доп. соглашений')
    
    def get_inlines(self, request, obj=None):
        if obj and obj.pk and not obj.type.is_supplementary:
            return [SupplementaryAgreementInline]
        return []
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.type.is_supplementary:
            form.base_fields['main_contract'].queryset = Contract.objects.filter(type__is_supplementary=False)
        else:
            form.base_fields['main_contract'].widget = forms.HiddenInput()
            form.base_fields['main_contract'].required = False
        return form
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/sync-rnd-status/', self.admin_site.admin_view(self.sync_rnd_status),
                 name='rnd_contract_sync_rnd_status'),
        ]
        return custom_urls + urls
    
    def sync_rnd_status(self, request, object_id):
        updated_count = update_all_rnd_statuses_for_contract(object_id)
        if updated_count > 0:
            self.message_user(request, _('Статусы {} НИОКР успешно синхронизированы с договором').format(updated_count),
                             messages.SUCCESS)
        else:
            self.message_user(request, _('Нет НИОКР для синхронизации или статус договора не изменился'),
                             messages.WARNING)
        return HttpResponseRedirect(reverse('admin:rnd_contract_change', args=[object_id]))
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        contract = self.get_object(request, object_id)
        if contract and not contract.type.is_supplementary:
            sync_url = reverse('admin:rnd_contract_sync_rnd_status', args=[object_id])
            extra_context['sync_button'] = format_html(
                '''
                <div style="margin: 10px 0;">
                    <a href="{}" class="button" style="background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; display: inline-block;">
                        🔄 {}
                    </a>
                </div>
                ''',
                sync_url,
                _('Синхронизировать статусы НИОКР')
            )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if not change:
            main_contract = obj.main_contract
            obj.main_contract = None
            super().save_model(request, obj, form, change)
            if not obj.type.is_supplementary:
                obj.main_contract = obj
                obj.save(update_fields=['main_contract'])
            else:
                obj.main_contract = main_contract
                obj.save(update_fields=['main_contract'])
        else:
            super().save_model(request, obj, form, change)
    
    class Media:
        css = {'all': ('css/admin_contract.css',)}


@admin.register(RnDType)
class RnDTypeAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'name', 'description_short', 'rnd_count')
    search_fields = ('name', 'short_name', 'description')
    list_display_links = ('short_name', 'name')
    fieldsets = ((None, {'fields': ('name', 'short_name', 'description')}),)
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(rnd_count=Count('rnd'))
    
    def description_short(self, obj):
        if obj.description and len(obj.description) > 100:
            return f"{obj.description[:100]}..."
        return obj.description or "-"
    description_short.short_description = _('Описание')
    
    def rnd_count(self, obj):
        count = obj.rnd_count if hasattr(obj, 'rnd_count') else obj.rnd_set.count()
        url = reverse('admin:rnd_rnd_changelist') + f'?type__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    rnd_count.short_description = _('НИОКР')


@admin.register(RnD)
class RnDAdmin(admin.ModelAdmin):
    list_display = ('uuid_display', 'code', 'title_short', 'contract_link', 'type_display', 'status_display', 'created_at')
    list_filter = ('status', 'type', 'contract__type')
    search_fields = ('uuid', 'code', 'title', 'purpose', 'contract__number')
    list_select_related = ('contract', 'type', 'contract__type')
    readonly_fields = ('created_at', 'updated_at', 'contract_info', 'last_contract_status')
    inlines = [TechnicalSpecificationInline, RnDTaskInline]
    
    fieldsets = (
        (_('Идентификация'), {'fields': ('uuid', 'code', 'title', 'type')}),
        (_('Договорная информация'), {'fields': ('contract', 'contract_info')}),
        (_('Содержание'), {'fields': ('purpose',)}),
        (_('Статус'), {
            'fields': ('status', 'last_contract_status'),
            'description': _(
                '<strong>В работе</strong> - НИОКР выполняется<br>'
                '<strong>Приостановлена</strong> - работа временно остановлена<br>'
                '<strong>Завершена</strong> - НИОКР успешно завершена<br>'
                '<strong>Контракт расторгнут</strong> - работа прекращена из-за расторжения контракта'
            )
        }),
        (_('Системная информация'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'contract', 'type', 'contract__type'
        ).prefetch_related('tasks', 'technical_specifications')
    
    def uuid_display(self, obj):
        return format_html(
            '<code style="font-size: 0.9em; background: #f5f5f5; padding: 2px 4px; border-radius: 3px;">{}</code>',
            obj.uuid
        )
    uuid_display.short_description = _('UUID')
    uuid_display.admin_order_field = 'uuid'
    
    def title_short(self, obj):
        if len(obj.title) > 50:
            return f"{obj.title[:50]}..."
        return obj.title
    title_short.short_description = _('Тема')
    title_short.admin_order_field = 'title'
    
    def contract_link(self, obj):
        url = reverse('admin:rnd_contract_change', args=[obj.contract.id])
        return format_html(
            '<a href="{}">{}</a><br><small>{}</small>',
            url, obj.contract.number, obj.contract.type.short_name
        )
    contract_link.short_description = _('Контракт')
    contract_link.admin_order_field = 'contract__number'
    
    def type_display(self, obj):
        return obj.type.short_name
    type_display.short_description = _('Тип работ')
    type_display.admin_order_field = 'type__short_name'
    
    def status_display(self, obj):
        status_colors = {
            'in_progress': '#4caf50',
            'suspended': '#ff9800',
            'completed': '#2196f3',
            'contract_terminated': '#f44336',
        }
        color = status_colors.get(obj.status, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = _('Статус')
    
    def contract_info(self, obj):
        contract = obj.contract
        url = reverse('admin:rnd_contract_change', args=[contract.id])
        return format_html(
            '''
            <div style="padding: 10px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #2196F3;">
                <strong>{}</strong><br>
                <strong>{}:</strong> {}<br>
                <strong>{}:</strong> {}<br>
                <strong>{}:</strong> {}<br>
                <a href="{}" class="button" style="margin-top: 5px;">{}</a>
            </div>
            ''',
            contract.display_name,
            _('Тип'), contract.type.name,
            _('Статус'), contract.get_status_display(),
            _('Дата подписания'), contract.signed_date,
            url, _('Перейти к договору')
        )
    contract_info.short_description = _('Информация о договоре')


@admin.register(TechnicalSpecification)
class TechnicalSpecificationAdmin(admin.ModelAdmin):
    list_display = ('rnd_uuid_display', 'version_display', 'contract_document_link', 'is_active_display', 
                   'file_info', 'uploaded_at')
    list_filter = ('is_active', ('contract_document__type__is_supplementary', admin.BooleanFieldListFilter), 
                  'contract_document__main_contract')
    search_fields = ('rnd__uuid', 'rnd__code', 'rnd__title', 'contract_document__number', 'description')
    list_select_related = ('rnd', 'contract_document', 'contract_document__type')
    readonly_fields = ('uploaded_at', 'file_path_info')
    
    fieldsets = (
        (_('Привязка'), {'fields': ('rnd', 'contract_document')}),
        (_('Техническое задание'), {'fields': ('version', 'document', 'description', 'is_active')}),
        (_('Информация о файле'), {'fields': ('file_path_info', 'uploaded_at'), 'classes': ('collapse',)}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'rnd', 'rnd__contract', 'contract_document', 'contract_document__type', 'contract_document__main_contract'
        )
    
    def rnd_uuid_display(self, obj):
        url = reverse('admin:rnd_rnd_change', args=[obj.rnd.id])
        return format_html(
            '''
            <div>
                <a href="{}"><strong>{}</strong></a><br>
                <small style="color: #666;">{}</small>
            </div>
            ''',
            url, obj.rnd.uuid, obj.rnd.code
        )
    rnd_uuid_display.short_description = _('НИОКР (UUID)')
    rnd_uuid_display.admin_order_field = 'rnd__uuid'
    
    def version_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; background: #e3f2fd; padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.version
        )
    version_display.short_description = _('Версия')
    
    def contract_document_link(self, obj):
        url = reverse('admin:rnd_contract_change', args=[obj.contract_document.id])
        if obj.contract_document.type.is_supplementary:
            return format_html(
                '''
                <div>
                    <a href="{}">ДС {}</a><br>
                    <small style="color: #666;">к {}</small>
                </div>
                ''',
                url, obj.contract_document.number, obj.contract_document.main_contract.number
            )
        else:
            return format_html('<a href="{}">{}</a>', url, obj.contract_document.number)
    contract_document_link.short_description = _('Документ-основание')
    contract_document_link.admin_order_field = 'contract_document__number'
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #4caf50; font-weight: bold;">✓ {}</span>', _('Актуальная'))
        return format_html('<span style="color: #999;">✗ {}</span>', _('Архивная'))
    is_active_display.short_description = _('Статус')
    
    def file_info(self, obj):
        if obj.document:
            filename = obj.document.name.split('/')[-1]
            return format_html(
                '''
                <div>
                    <strong>{}</strong><br>
                    <small style="color: #666; font-family: monospace;">{}</small>
                </div>
                ''',
                filename, obj.file_structure_info
            )
        return "-"
    file_info.short_description = _('Файл')
    
    def file_path_info(self, obj):
        if obj.document:
            return format_html(
                '''
                <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
                    <strong>{}:</strong><br>
                    <code style="display: block; margin: 5px 0; padding: 8px; background: white; border: 1px solid #ddd;">{}</code>
                    <strong>{}:</strong> {}<br>
                    <strong>{}:</strong> {}<br>
                    <strong>{}:</strong> {}
                </div>
                ''',
                _('Полный путь'),
                obj.document.path if hasattr(obj.document, 'path') else obj.document.name,
                _('Размер'), self.get_file_size(obj.document),
                _('Тип'), self.get_file_type(obj.document),
                _('Загружен'), obj.uploaded_at.strftime('%d.%m.%Y %H:%M')
            )
        return _('Файл не загружен')
    
    def get_file_size(self, file):
        try:
            size = file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except (OSError, ValueError):
            return _('Неизвестно')
    
    def get_file_type(self, file):
        name = file.name.lower()
        if name.endswith('.pdf'):
            return 'PDF'
        elif name.endswith('.doc') or name.endswith('.docx'):
            return 'Word'
        elif name.endswith('.xls') or name.endswith('.xlsx'):
            return 'Excel'
        else:
            return _('Другой')


@admin.register(RnDTask)
class RnDTaskAdmin(admin.ModelAdmin):
    list_display = ('rnd_info', 'order_display', 'description_short', 'source_specification_display', 
                   'is_completed_display', 'created_at')
    list_filter = ('is_completed', 'rnd__contract', 'source_specification')
    search_fields = ('description', 'rnd__uuid', 'rnd__code', 'rnd__title', 'source_specification__version')
    list_select_related = ('rnd', 'source_specification', 'rnd__contract')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Привязка'), {'fields': ('rnd', 'source_specification', 'order')}),
        (_('Содержание задачи'), {'fields': ('description', 'is_completed')}),
        (_('Системная информация'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'rnd', 'rnd__contract', 'source_specification', 'source_specification__contract_document'
        )
    
    def rnd_info(self, obj):
        url = reverse('admin:rnd_rnd_change', args=[obj.rnd.id])
        return format_html(
            '''
            <div>
                <a href="{}"><strong>{}</strong></a><br>
                <small style="color: #666;">{}: {}</small>
            </div>
            ''',
            url, obj.rnd.uuid, obj.rnd.code, obj.rnd.title[:30] + ('...' if len(obj.rnd.title) > 30 else '')
        )
    rnd_info.short_description = _('НИОКР')
    rnd_info.admin_order_field = 'rnd__uuid'
    
    def order_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #2196F3;">{}</span>', obj.order)
    order_display.short_description = _('№')
    order_display.admin_order_field = 'order'
    
    def description_short(self, obj):
        if len(obj.description) > 80:
            return f"{obj.description[:80]}..."
        return obj.description
    description_short.short_description = _('Описание')
    
    def source_specification_display(self, obj):
        if obj.source_specification:
            url = reverse('admin:rnd_technicalspecification_change', args=[obj.source_specification.id])
            return format_html('<a href="{}">вер.{}</a>', url, obj.source_specification.version)
        return format_html('<span style="color: #999;">{}</span>', _('нет'))
    source_specification_display.short_description = _('Источник (ТЗ)')
    
    def is_completed_display(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: #4caf50; font-weight: bold;">✓ {}</span>', _('Выполнена'))
        return format_html('<span style="color: #ff9800;">● {}</span>', _('В работе'))
    is_completed_display.short_description = _('Статус')


admin.site.site_header = _('Управление НИОКР')
admin.site.site_title = _('Администрирование НИОКР')
admin.site.index_title = _('Панель управления')