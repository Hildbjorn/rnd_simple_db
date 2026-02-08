"""
Модели приложения.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .utils import UploadPathFactory


class ContractType(models.Model):
    """Типы договоров."""
    name = models.CharField(max_length=255, verbose_name=_('Тип договора (полностью)'))
    short_name = models.CharField(max_length=100, verbose_name=_('Тип договора (кратко)'))
    is_supplementary = models.BooleanField(default=False, verbose_name=_('Является дополнительным соглашением'))
    parent_type = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='child_types', verbose_name=_('Родительский тип договора'))
    description = models.TextField(verbose_name=_('Описание'), blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.is_supplementary and not self.parent_type:
            raise ValidationError({
                'parent_type': _('Для дополнительного соглашения необходимо указать родительский тип договора')
            })
        if self.is_supplementary and self.parent_type.is_supplementary:
            raise ValidationError({
                'parent_type': _('Родительский тип не может быть дополнительным соглашением')
            })
        if self.parent_type and self.parent_type.id == self.id:
            raise ValidationError({'parent_type': _('Тип не может ссылаться сам на себя')})
    
    @property
    def is_main_contract_type(self):
        return not self.is_supplementary
    
    class Meta:
        verbose_name = _('Тип договора')
        verbose_name_plural = _('Типы договоров')
        ordering = ['is_supplementary', 'short_name']
        indexes = [
            models.Index(fields=['short_name']),
            models.Index(fields=['is_supplementary']),
        ]


class Contract(models.Model):
    """Контракт или связанный договор."""
    CONTRACT_STATUS_CHOICES = [
        ('active', _('Действующий')),
        ('suspended', _('Приостановлен')),
        ('completed', _('Завершен')),
        ('terminated', _('Расторгнут')),
    ]
    
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='next_versions', verbose_name=_('Предыдущая версия'))
    main_contract = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                    related_name='related_documents', verbose_name=_('Основной договор'))
    type = models.ForeignKey(ContractType, on_delete=models.PROTECT, related_name='contracts', 
                           verbose_name=_('Тип договора'))
    number = models.CharField(max_length=255, unique=True, verbose_name=_('Номер договора'))
    name = models.CharField(max_length=500, verbose_name=_('Наименование договора'), blank=True, null=True)
    signed_date = models.DateField(verbose_name=_('Дата подписания'))
    effective_date = models.DateField(verbose_name=_('Дата вступления в силу'))
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default='active', 
                            verbose_name=_('Статус договора'))
    document = models.FileField(upload_to=UploadPathFactory.for_contract_document, blank=True, null=True, 
                              max_length=500, verbose_name=_('Скан договора'))
    description = models.TextField(verbose_name=_('Описание/комментарий'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.type.is_supplementary:
            return f"ДС {self.number} к {self.main_contract.number}"
        return f"{self.number} ({self.type.short_name})"
    
    def clean(self):
        if not self.number or not self.number.strip():
            raise ValidationError({'number': _('Номер договора обязателен для заполнения')})
        
        if self.type and self.type.is_supplementary:
            if not self.main_contract:
                raise ValidationError({
                    'main_contract': _('Для дополнительного соглашения необходимо указать основной договор')
                })
            if self.main_contract.type.is_supplementary:
                raise ValidationError({
                    'main_contract': _('Основной договор не может быть дополнительным соглашением')
                })
            if self.main_contract.type != self.type.parent_type:
                raise ValidationError({
                    'main_contract': _(f'Тип основного договора должен быть "{self.type.parent_type}"')
                })
        else:
            if self.main_contract and self.main_contract.id and self.main_contract.id != self.id:
                raise ValidationError({
                    'main_contract': _('Основной договор не может ссылаться на другой договор')
                })
        
        if self.previous_version and self.previous_version.id == self.id:
            raise ValidationError({'previous_version': _('Договор не может ссылаться сам на себя')})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        
        if not self.type.is_supplementary and is_new:
            main_contract = self.main_contract
            self.main_contract = None
            super().save(*args, **kwargs)
            self.main_contract = self
            super().save(update_fields=['main_contract'])
        else:
            super().save(*args, **kwargs)
    
    @property
    def is_supplementary(self):
        return self.type.is_supplementary
    
    @property
    def is_main_contract(self):
        return not self.is_supplementary
    
    @property
    def display_name(self):
        if self.name:
            return f"{self.number} - {self.name}"
        return str(self)
    
    @property
    def contract_status(self):
        if self.is_main_contract:
            return self.status
        return self.main_contract.status
    
    class Meta:
        verbose_name = _('Договор')
        verbose_name_plural = _('Договоры')
        ordering = ['-signed_date', 'number']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
            models.Index(fields=['main_contract']),
        ]


class RnDType(models.Model):
    """Типы научно-исследовательских и опытно-конструкторских работ."""
    name = models.CharField(max_length=255, verbose_name=_('Название типа работ'))
    short_name = models.CharField(max_length=100, verbose_name=_('Краткое название'))
    description = models.TextField(verbose_name=_('Описание'), blank=True, null=True)
    
    def __str__(self):
        return self.short_name
    
    class Meta:
        verbose_name = _('Тип НИОКР')
        verbose_name_plural = _('Типы НИОКР')
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]


class RnD(models.Model):
    """Научно-исследовательская или опытно-конструкторская работа."""
    STATUS_CHOICES = [
        ('in_progress', _('В работе')),
        ('suspended', _('Приостановлена')),
        ('completed', _('Завершена')),
        ('contract_terminated', _('Контракт расторгнут')),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name='rnd_works', 
                               verbose_name=_('Основной договор'))
    type = models.ForeignKey(RnDType, on_delete=models.PROTECT, verbose_name=_('Тип работ'))
    uuid = models.SlugField(max_length=100, unique=True, db_index=True, verbose_name=_('UUID (идентификатор)'))
    code = models.CharField(max_length=100, verbose_name=_('Шифр работы'))
    title = models.CharField(max_length=500, verbose_name=_('Тема работы'))
    purpose = models.TextField(verbose_name=_('Цель работы'), blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', 
                            verbose_name=_('Статус НИОКР'))
    last_contract_status = models.CharField(max_length=20, choices=Contract.CONTRACT_STATUS_CHOICES, 
                                          blank=True, null=True, editable=False, 
                                          verbose_name=_('Последний статус договора'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code}: {self.title}"
    
    def clean(self):
        if self.contract and self.contract.type.is_supplementary:
            raise ValidationError({
                'contract': _('НИОКР можно привязать только к основному договору')
            })
        if not self.uuid or not self.uuid.strip():
            raise ValidationError({'uuid': _('UUID обязателен для заполнения')})
        self.sync_status_with_contract()
    
    def sync_status_with_contract(self, force=False):
        """Синхронизация статуса НИОКР со статусом договора."""
        if not self.contract:
            return False
        
        contract_status = self.contract.status
        if not force and self.last_contract_status == contract_status:
            return False
        
        status_mapping = {
            'active': 'in_progress',
            'suspended': 'suspended',
            'completed': 'completed',
            'terminated': 'contract_terminated',
        }
        new_status = status_mapping.get(contract_status, 'in_progress')
        
        if self.status != new_status or force:
            self.status = new_status
            self.last_contract_status = contract_status
            return True
        return False
    
    def save(self, *args, **kwargs):
        self.full_clean()
        if self.pk:
            self.sync_status_with_contract()
        else:
            self.sync_status_with_contract(force=True)
        super().save(*args, **kwargs)
    
    @property
    def contract_number(self):
        return self.contract.number
    
    @property
    def contract_type(self):
        return self.contract.type.short_name
    
    @property
    def contract_status(self):
        return self.contract.get_status_display()
    
    class Meta:
        verbose_name = _('НИОКР')
        verbose_name_plural = _('НИОКР')
        ordering = ['-created_at']
        unique_together = [['contract', 'code']]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['code']),
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['uuid']),
        ]


class TechnicalSpecification(models.Model):
    """Техническое задание (файл ТЗ) с привязкой к договору."""
    
    def get_upload_path(self, filename):
        """Генерирует короткий путь для загрузки файла ТЗ."""
        return UploadPathFactory.for_technical_specification(self, filename)
    
    rnd = models.ForeignKey(RnD, on_delete=models.CASCADE, related_name='technical_specifications', 
                          verbose_name=_('НИОКР'))
    contract_document = models.ForeignKey(Contract, on_delete=models.PROTECT, 
                                        related_name='technical_specifications', 
                                        verbose_name=_('Договор-основание'))
    document = models.FileField(upload_to=get_upload_path, verbose_name=_('Файл ТЗ'))
    version = models.CharField(max_length=20, default='1.0', verbose_name=_('Версия ТЗ'))
    is_active = models.BooleanField(default=True, verbose_name=_('Актуальная версия'))
    description = models.TextField(verbose_name=_('Описание изменений'), blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"ТЗ вер.{self.version} для {self.rnd.code}"
    
    def clean(self):
        if self.rnd and self.contract_document:
            if self.contract_document.is_main_contract:
                if self.contract_document != self.rnd.contract:
                    raise ValidationError({
                        'contract_document': _('Основной договор должен совпадать с договором НИОКР')
                    })
            else:
                if self.contract_document.main_contract != self.rnd.contract:
                    raise ValidationError({
                        'contract_document': _('Дополнительное соглашение должно относиться к тому же основному договору')
                    })
        
        if self.is_active and self.rnd:
            TechnicalSpecification.objects.filter(
                rnd=self.rnd, is_active=True
            ).exclude(id=self.id).update(is_active=False)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def display_name(self):
        return f"{self.rnd.code} - ТЗ вер.{self.version}"
    
    @property
    def document_type(self):
        return self.contract_document.type.short_name
    
    @property
    def document_number(self):
        return self.contract_document.number
    
    @property
    def rnd_uuid(self):
        return self.rnd.uuid
    
    @property
    def file_path_display(self):
        if self.document:
            return str(self.document)
        return "-"
    
    @property
    def file_structure_info(self):
        if self.rnd and self.document:
            current_date = self.uploaded_at.strftime('%Y_%m_%d')
            folder_name = f"{self.rnd.uuid}_ts_{current_date}"
            return f"{self.rnd.uuid}/technical_specifications/ts/{folder_name}/"
        return "Не определено"
    
    class Meta:
        verbose_name = _('Техническое задание')
        verbose_name_plural = _('Технические задания')
        ordering = ['rnd', '-is_active', '-version']
        indexes = [
            models.Index(fields=['rnd', 'is_active']),
            models.Index(fields=['contract_document']),
        ]


class RnDTask(models.Model):
    """Задача в рамках НИОКР."""
    rnd = models.ForeignKey(RnD, on_delete=models.CASCADE, related_name='tasks', verbose_name=_('НИОКР'))
    source_specification = models.ForeignKey(TechnicalSpecification, on_delete=models.SET_NULL, 
                                           null=True, blank=True, related_name='tasks', 
                                           verbose_name=_('Источник (ТЗ)'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Порядковый номер'))
    description = models.TextField(verbose_name=_('Описание задачи'))
    is_completed = models.BooleanField(default=False, verbose_name=_('Выполнена'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Задача {self.order}: {self.description[:50]}..."
    
    def clean(self):
        if self.source_specification and self.source_specification.rnd != self.rnd:
            raise ValidationError({
                'source_specification': _('ТЗ должно относиться к тому же НИОКР')
            })
    
    @property
    def rnd_uuid(self):
        return self.rnd.uuid
    
    class Meta:
        verbose_name = _('Задача НИОКР')
        verbose_name_plural = _('Задачи НИОКР')
        ordering = ['rnd', 'order']
        unique_together = [['rnd', 'order']]
        indexes = [models.Index(fields=['rnd', 'is_completed'])]


# Функция для обновления статусов НИОКР
def update_all_rnd_statuses_for_contract(contract_id):
    """Вспомогательная функция для принудительного обновления статусов НИОКР."""
    try:
        contract = Contract.objects.get(pk=contract_id, is_main_contract=True)
        status_mapping = {
            'active': 'in_progress',
            'suspended': 'suspended',
            'completed': 'completed',
            'terminated': 'contract_terminated',
        }
        new_status = status_mapping.get(contract.status, 'in_progress')
        updated_count = RnD.objects.filter(contract=contract).update(
            status=new_status,
            last_contract_status=contract.status
        )
        return updated_count
    except Contract.DoesNotExist:
        return 0