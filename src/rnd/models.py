"""
Модели приложения.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .utils import UploadPathFactory


class ContractType(models.Model):
    """
    Типы договоров.
    Определяет, является ли договор основным или дополнительным соглашением.
    """
    
    name = models.CharField(
        max_length=255,
        verbose_name=_('Тип договора (полностью)'),
        help_text=_('Полное название типа договора')
    )
    
    short_name = models.CharField(
        max_length=100,
        verbose_name=_('Тип договора (кратко)'),
        help_text=_('Краткое название типа договора для отображения в списках')
    )
    
    is_supplementary = models.BooleanField(
        default=False,
        verbose_name=_('Является дополнительным соглашением'),
        help_text=_('Отметьте для типов, которые являются дополнительными соглашениями')
    )
    
    parent_type = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_types',
        verbose_name=_('Родительский тип договора'),
        help_text=_('Для доп. соглашений укажите тип основного договора')
    )
    
    description = models.TextField(
        verbose_name=_('Описание'),
        blank=True,
        null=True,
        help_text=_('Подробное описание типа договора')
    )
    
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
            raise ValidationError({
                'parent_type': _('Тип не может ссылаться сам на себя')
            })
    
    @property
    def is_main_contract_type(self):
        """Является ли тип основным договором."""
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
    """
    Контракт или связанный договор.
    Может быть основным договором или дополнительным соглашением.
    """
    
    CONTRACT_STATUS_CHOICES = [
        ('active', _('Действующий')),
        ('suspended', _('Приостановлен')),
        ('completed', _('Завершен')),
        ('terminated', _('Расторгнут')),
    ]
    
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
        verbose_name=_('Предыдущая версия'),
        help_text=_('Предыдущая версия этого договора')
    )
    
    main_contract = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='related_documents',
        verbose_name=_('Основной договор'),
        help_text=_('Основной договор, к которому относится данный договор')
    )
    
    type = models.ForeignKey(
        ContractType,
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name=_('Тип договора'),
        help_text=_('Тип договора (договор, доп. соглашение и т.д.)')
    )
    
    number = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('Номер договора'),
        help_text=_('Уникальный номер договора')
    )
    
    name = models.CharField(
        max_length=500,
        verbose_name=_('Наименование договора'),
        blank=True,
        null=True,
        help_text=_('Полное наименование договора')
    )
    
    signed_date = models.DateField(
        verbose_name=_('Дата подписания'),
        help_text=_('Дата подписания договора')
    )
    
    effective_date = models.DateField(
        verbose_name=_('Дата вступления в силу'),
        help_text=_('Дата, с которой договор действует')
    )
    
    status = models.CharField(
        max_length=20,
        choices=CONTRACT_STATUS_CHOICES,
        default='active',
        verbose_name=_('Статус договора'),
        help_text=_('Текущий статус договора')
    )
    
    document = models.FileField(
        upload_to=UploadPathFactory.for_contract_document,
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Скан договора'),
        help_text=_('Отсканированная копия договора')
    )
    
    description = models.TextField(
        verbose_name=_('Описание/комментарий'),
        blank=True,
        null=True,
        help_text=_('Описание договора или внесенных изменений')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.type.is_supplementary:
            return f"ДС {self.number} к {self.main_contract.number}"
        return f"{self.number} ({self.type.short_name})"
    
    def clean(self):
        if not self.number or not self.number.strip():
            raise ValidationError({
                'number': _('Номер договора обязателен для заполнения')
            })
        
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
                    'main_contract': _(
                        f'Тип основного договора должен быть "{self.type.parent_type}"'
                    )
                })
        else:
            if self.main_contract and self.main_contract.id and self.main_contract.id != self.id:
                raise ValidationError({
                    'main_contract': _('Основной договор не может ссылаться на другой договор')
                })
        
        if self.previous_version and self.previous_version.id == self.id:
            raise ValidationError({
                'previous_version': _('Договор не может ссылаться сам на себя')
            })
    
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
        """Является ли договор дополнительным соглашением."""
        return self.type.is_supplementary
    
    @property
    def is_main_contract(self):
        """Является ли договор основным договором."""
        return not self.is_supplementary
    
    @property
    def display_name(self):
        """Отображаемое имя договора."""
        if self.name:
            return f"{self.number} - {self.name}"
        return str(self)
    
    @property
    def contract_status(self):
        """Статус основного договора."""
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
    """
    Типы научно-исследовательских и опытно-конструкторских работ.
    """
    
    name = models.CharField(
        max_length=255,
        verbose_name=_('Название типа работ'),
        help_text=_('Полное название типа НИОКР')
    )
    
    short_name = models.CharField(
        max_length=100,
        verbose_name=_('Краткое название'),
        help_text=_('Краткое обозначение типа работ')
    )
    
    description = models.TextField(
        verbose_name=_('Описание'),
        blank=True,
        null=True,
        help_text=_('Подробное описание типа работ')
    )
    
    def __str__(self):
        return self.short_name
    
    class Meta:
        verbose_name = _('Тип НИОКР')
        verbose_name_plural = _('Типы НИОКР')
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]


class RnD(models.Model):
    """
    Научно-исследовательская или опытно-конструкторская работа.
    Статус НИОКР автоматически синхронизируется со статусом договора.
    """
    
    STATUS_CHOICES = [
        ('in_progress', _('В работе')),
        ('suspended', _('Приостановлена')),
        ('completed', _('Завершена')),
        ('contract_terminated', _('Контракт расторгнут')),
    ]
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.PROTECT,
        related_name='rnd_works',
        verbose_name=_('Основной договор'),
        help_text=_('Основной договор, по которому ведется НИОКР')
    )
    
    type = models.ForeignKey(
        RnDType,
        on_delete=models.PROTECT,
        verbose_name=_('Тип работ'),
        help_text=_('Тип научно-исследовательских работ')
    )
    
    uuid = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name=_('UUID (идентификатор)'),
        help_text=_('Уникальный идентификатор НИОКР для внешних ссылок. Заполняется вручную.')
    )
    
    code = models.CharField(
        max_length=100,
        verbose_name=_('Шифр работы'),
        help_text=_('Уникальный шифр работы согласно контракту')
    )
    
    title = models.CharField(
        max_length=500,
        verbose_name=_('Тема работы'),
        help_text=_('Полное наименование темы работы')
    )
    
    purpose = models.TextField(
        verbose_name=_('Цель работы'),
        blank=True,
        null=True,
        help_text=_('Основные цели и задачи работы')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name=_('Статус НИОКР'),
        help_text=_('Текущий статус выполнения работы')
    )
    
    last_contract_status = models.CharField(
        max_length=20,
        choices=Contract.CONTRACT_STATUS_CHOICES,
        blank=True,
        null=True,
        editable=False,
        verbose_name=_('Последний статус договора'),
        help_text=_('Статус договора на момент последней синхронизации')
    )
    
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
            raise ValidationError({
                'uuid': _('UUID обязателен для заполнения')
            })
        
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
        """Номер контракта."""
        return self.contract.number
    
    @property
    def contract_type(self):
        """Тип контракта."""
        return self.contract.type.short_name
    
    @property
    def contract_status(self):
        """Статус контракта."""
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
    """
    Техническое задание (файл ТЗ) с привязкой к договору.
    """
    
    def get_upload_path(self, filename):
        """Генерирует короткий путь для загрузки файла ТЗ."""
        return UploadPathFactory.for_technical_specification(self, filename)
    
    rnd = models.ForeignKey(
        RnD,
        on_delete=models.CASCADE,
        related_name='technical_specifications',
        verbose_name=_('НИОКР'),
        help_text=_('НИОКР, к которому относится ТЗ')
    )
    
    contract_document = models.ForeignKey(
        Contract,
        on_delete=models.PROTECT,
        related_name='technical_specifications',
        verbose_name=_('Договор-основание'),
        help_text=_('Договор, которым утверждено ТЗ (договор или доп. соглашение)')
    )
    
    document = models.FileField(
        upload_to=get_upload_path,
        verbose_name=_('Файл ТЗ'),
        help_text=_('Отсканированное техническое задание в формате PDF')
    )
    
    version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name=_('Версия ТЗ'),
        help_text=_('Версия ТЗ (например: 1.0, 2.1, Исправленная)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Актуальная версия'),
        help_text=_('Является ли эта версия ТЗ действующей')
    )
    
    description = models.TextField(
        verbose_name=_('Описание изменений'),
        blank=True,
        null=True,
        help_text=_('Что изменилось в этой версии ТЗ')
    )
    
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
                        'contract_document': _(
                            'Дополнительное соглашение должно относиться '
                            'к тому же основному договору, что и НИОКР'
                        )
                    })
        
        if self.is_active and self.rnd:
            TechnicalSpecification.objects.filter(
                rnd=self.rnd,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def display_name(self):
        """Отображаемое имя ТЗ."""
        return f"{self.rnd.code} - ТЗ вер.{self.version}"
    
    @property
    def document_type(self):
        """Тип договора-основания."""
        return self.contract_document.type.short_name
    
    @property
    def document_number(self):
        """Номер договора-основания."""
        return self.contract_document.number
    
    @property
    def rnd_uuid(self):
        """UUID НИОКР для удобства."""
        return self.rnd.uuid
    
    @property
    def file_path_display(self):
        """Отображаемый путь к файлу."""
        if self.document:
            return str(self.document)
        return "-"
    
    @property
    def file_structure_info(self):
        """Информация о структуре хранения файла."""
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
    """
    Задача в рамках НИОКР.
    """
    
    rnd = models.ForeignKey(
        RnD,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_('НИОКР'),
        help_text=_('НИОКР, к которой относится задача')
    )
    
    source_specification = models.ForeignKey(
        TechnicalSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name=_('Источник (ТЗ)'),
        help_text=_('Техническое задание, из которого взята задача (для справки)')
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Порядковый номер'),
        help_text=_('Порядок отображения задачи в списке')
    )
    
    description = models.TextField(
        verbose_name=_('Описание задачи'),
        help_text=_('Подробное описание задачи и требований к выполнению')
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Выполнена'),
        help_text=_('Отметка о выполнении задачи')
    )
    
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
        """UUID НИОКР для удобства."""
        return self.rnd.uuid
    
    class Meta:
        verbose_name = _('Задача НИОКР')
        verbose_name_plural = _('Задачи НИОКР')
        ordering = ['rnd', 'order']
        unique_together = [['rnd', 'order']]
        indexes = [models.Index(fields=['rnd', 'is_completed'])]


# Функция для обновления статусов НИОКР
def update_all_rnd_statuses_for_contract(contract_id):
    """
    Вспомогательная функция для принудительного обновления статусов НИОКР.
    Может быть использована в админке или через команду.
    """
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