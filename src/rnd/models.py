import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db.models import F
from django.utils import timezone


class ContractType(models.Model):
    """
    Типы договоров и документов.
    """
    
    name = models.CharField(
        max_length=255,
        verbose_name=_('Тип документа (полностью)'),
        help_text=_('Полное название типа документа')
    )
    
    short_name = models.CharField(
        max_length=100,
        verbose_name=_('Тип документа (кратко)'),
        help_text=_('Краткое название типа документа для отображения в списках')
    )
    
    is_supplementary = models.BooleanField(
        default=False,
        verbose_name=_('Является дополнительным соглашением'),
        help_text=_('Отметьте для типов, которые являются дополнительными соглашениями')
    )
    
    parent_type = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        verbose_name=_('Родительский тип договора'),
        null=True,
        blank=True,
        related_name='child_types',
        help_text=_('Для доп. соглашений укажите тип основного договора')
    )
    
    description = models.TextField(
        verbose_name=_('Описание'),
        blank=True,
        null=True,
        help_text=_('Подробное описание типа документа')
    )
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Валидация типа договора."""
        if self.is_supplementary and not self.parent_type:
            raise ValidationError({
                'parent_type': _('Для дополнительного соглашения необходимо указать родительский тип договора')
            })
        
        if self.is_supplementary and self.parent_type.is_supplementary:
            raise ValidationError({
                'parent_type': _('Родительский тип не может быть дополнительным соглашением')
            })
        
        # Проверка на циклические ссылки
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
    Контракт или связанный документ.
    """
    
    CONTRACT_STATUS_CHOICES = [
        ('active', _('Действующий')),
        ('suspended', _('Приостановлен')),
        ('completed', _('Завершен')),
        ('terminated', _('Расторгнут')),
    ]
    
    # Связь с предыдущей версией документа
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        verbose_name=_('Предыдущая версия'),
        related_name='next_versions',
        null=True,
        blank=True,
        help_text=_('Предыдущая версия этого документа')
    )
    
    # Основной договор (для дополнительных соглашений)
    main_contract = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        verbose_name=_('Основной договор'),
        related_name='related_documents',
        null=True,
        blank=True,
        help_text=_('Основной договор, к которому относится данный документ')
    )
    
    type = models.ForeignKey(
        ContractType,
        on_delete=models.PROTECT,
        verbose_name=_('Тип документа'),
        related_name='contracts',
        help_text=_('Тип документа (договор, доп. соглашение и т.д.)')
    )
    
    number = models.CharField(
        max_length=255,
        verbose_name=_('Номер документа'),
        unique=True,
        help_text=_('Уникальный номер документа')
    )
    
    name = models.CharField(
        max_length=500,
        verbose_name=_('Наименование документа'),
        help_text=_('Полное наименование документа'),
        blank=True,
        null=True
    )
    
    signed_date = models.DateField(
        verbose_name=_('Дата подписания'),
        help_text=_('Дата подписания документа')
    )
    
    effective_date = models.DateField(
        verbose_name=_('Дата вступления в силу'),
        help_text=_('Дата, с которой документ действует')
    )
    
    status = models.CharField(
        max_length=20,
        choices=CONTRACT_STATUS_CHOICES,
        default='active',
        verbose_name=_('Статус документа')
    )
    
    document = models.FileField(
        upload_to='contracts/%Y/%m/',
        verbose_name=_('Скан документа'),
        help_text=_('Отсканированная копия документа'),
        blank=True,
        null=True
    )
    
    description = models.TextField(
        verbose_name=_('Описание/комментарий'),
        blank=True,
        null=True,
        help_text=_('Описание документа или внесенных изменений')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.type.is_supplementary:
            return f"ДС {self.number} к {self.main_contract.number}"
        return f"{self.number} ({self.type.short_name})"
    
    def clean(self):
        """Валидация контракта."""
        if not self.number or not self.number.strip():
            raise ValidationError({
                'number': _('Номер документа обязателен для заполнения')
            })
        
        # Проверка типа документа
        if self.type.is_supplementary:
            # Для доп. соглашений должен быть указан основной договор
            if not self.main_contract:
                raise ValidationError({
                    'main_contract': _('Для дополнительного соглашения необходимо указать основной договор')
                })
            
            # Основной договор не должен быть доп. соглашением
            if self.main_contract.type.is_supplementary:
                raise ValidationError({
                    'main_contract': _('Основной договор не может быть дополнительным соглашением')
                })
            
            # Проверка соответствия типов
            if self.main_contract.type != self.type.parent_type:
                raise ValidationError({
                    'main_contract': _(
                        f'Тип основного договора должен быть "{self.type.parent_type}", '
                        f'а не "{self.main_contract.type}"'
                    )
                })
        else:
            # Основной договор не должен ссылаться на другой договор
            if self.main_contract and self.main_contract.id != self.id:
                raise ValidationError({
                    'main_contract': _('Основной договор не может ссылаться на другой договор')
                })
            self.main_contract = self
        
        # Проверка на циклические ссылки
        if self.previous_version and self.previous_version.id == self.id:
            raise ValidationError({
                'previous_version': _('Документ не может ссылаться сам на себя')
            })
    
    def save(self, *args, **kwargs):
        """Сохранение с дополнительной логикой."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_supplementary(self):
        """Является ли документ дополнительным соглашением."""
        return self.type.is_supplementary
    
    @property
    def is_main_contract(self):
        """Является ли документ основным договором."""
        return not self.is_supplementary
    
    @property
    def display_name(self):
        """Отображаемое имя документа."""
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
        verbose_name = _('Документ')
        verbose_name_plural = _('Документы')
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
        indexes = [
            models.Index(fields=['name']),
        ]


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
        verbose_name=_('Основной договор'),
        related_name='rnd_works',
        help_text=_('Основной договор, по которому ведется НИОКР')
    )
    
    type = models.ForeignKey(
        RnDType,
        on_delete=models.PROTECT,
        verbose_name=_('Тип работ'),
        help_text=_('Тип научно-исследовательских работ')
    )
    
    # Уникальный идентификатор для внешних ссылок (заполняется вручную)
    uuid = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_('UUID (идентификатор)'),
        help_text=_('Уникальный идентификатор НИОКР для внешних ссылок. Заполняется вручную.'),
        blank=False,
        null=False,
        db_index=True
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
        verbose_name=_('Статус НИОКР')
    )
    
    # Поле для отслеживания статуса договора
    last_contract_status = models.CharField(
        max_length=20,
        choices=Contract.CONTRACT_STATUS_CHOICES,
        blank=True,
        null=True,
        editable=False,
        verbose_name=_('Последний статус договора')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code}: {self.title}"
    
    def clean(self):
        """Валидация НИОКР."""
        # Проверка, что выбран основной договор (не доп. соглашение)
        if self.contract and self.contract.type.is_supplementary:
            raise ValidationError({
                'contract': _('НИОКР можно привязать только к основному договору')
            })
        
        # Проверка UUID
        if not self.uuid or not self.uuid.strip():
            raise ValidationError({
                'uuid': _('UUID обязателен для заполнения')
            })
        
        # Автоматическая синхронизация статуса с договором
        self.sync_status_with_contract()
    
    def sync_status_with_contract(self, force=False):
        """Синхронизация статуса НИОКР со статусом договора."""
        if not self.contract:
            return False
        
        contract_status = self.contract.status
        
        # Проверяем, изменился ли статус договора
        if not force and self.last_contract_status == contract_status:
            return False
        
        status_mapping = {
            'active': 'in_progress',
            'suspended': 'suspended',
            'completed': 'completed',
            'terminated': 'contract_terminated',
        }
        
        new_status = status_mapping.get(contract_status, 'in_progress')
        
        # Обновляем статус, если он изменился
        if self.status != new_status or force:
            self.status = new_status
            self.last_contract_status = contract_status
            return True
        
        return False
    
    def save(self, *args, **kwargs):
        """Сохранение с валидацией и синхронизацией статуса."""
        self.full_clean()
        
        # Синхронизируем статус перед сохранением
        if self.pk:  # Только для существующих объектов
            self.sync_status_with_contract()
        else:  # Для новых объектов
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
    Техническое задание (файл ТЗ) с привязкой к документу.
    """
    
    def get_upload_path(self, filename):
        """
        Генерирует путь для загрузки файла ТЗ.
        Формат: {rnd_uuid}/technical_specifications/ts/{uuid_ts_дата}/{filename}
        """
        if self.rnd:
            # Получаем текущую дату в формате YYYY_MM_DD
            current_date = timezone.now().strftime('%Y_%m_%d')
            
            # Формируем имя папки: uuid_ts_дата
            folder_name = f"{self.rnd.uuid}_ts_{current_date}"
            
            # Формируем полный путь
            return os.path.join(
                str(self.rnd.uuid),           # UUID НИОКР
                'technical_specifications',    # Папка для ТЗ
                'ts',                         # Подпапка ts
                folder_name,                  # Папка с датой
                filename
            )
        else:
            # Запасной путь, если НИОКР еще не установлен
            current_date = timezone.now().strftime('%Y_%m_%d')
            return os.path.join(
                'temp',
                'technical_specifications',
                current_date,
                filename
            )
    
    rnd = models.ForeignKey(
        RnD,
        on_delete=models.CASCADE,
        verbose_name=_('НИОКР'),
        related_name='technical_specifications',
        help_text=_('НИОКР, к которому относится ТЗ')
    )
    
    # Связь с документом (основным договором или доп. соглашением)
    contract_document = models.ForeignKey(
        Contract,
        on_delete=models.PROTECT,
        verbose_name=_('Документ-основание'),
        related_name='technical_specifications',
        help_text=_('Документ, которым утверждено ТЗ (договор или доп. соглашение)')
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
        """Валидация ТЗ."""
        # Проверка, что документ относится к тому же основному договору, что и НИОКР
        if self.rnd and self.contract_document:
            if self.contract_document.is_main_contract:
                # Если документ - основной договор
                if self.contract_document != self.rnd.contract:
                    raise ValidationError({
                        'contract_document': _(
                            'Основной договор должен совпадать с договором НИОКР'
                        )
                    })
            else:
                # Если документ - доп. соглашение
                if self.contract_document.main_contract != self.rnd.contract:
                    raise ValidationError({
                        'contract_document': _(
                            'Дополнительное соглашение должно относиться к тому же основному договору, '
                            'что и НИОКР'
                        )
                    })
        
        # Автоматическая деактивация старых версий при активации новой
        if self.is_active and self.rnd:
            TechnicalSpecification.objects.filter(
                rnd=self.rnd,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
    
    def save(self, *args, **kwargs):
        """Сохранение с валидацией."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def display_name(self):
        """Отображаемое имя ТЗ."""
        return f"{self.rnd.code} - ТЗ вер.{self.version}"
    
    @property
    def document_type(self):
        """Тип документа-основания."""
        return self.contract_document.type.short_name
    
    @property
    def document_number(self):
        """Номер документа-основания."""
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
        verbose_name=_('НИОКР'),
        related_name='tasks'
    )
    
    # Связь с ТЗ (опциональная, для информации о том, из какого ТЗ взята задача)
    source_specification = models.ForeignKey(
        TechnicalSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Источник (ТЗ)'),
        related_name='tasks',
        help_text=_('Техническое задание, из которого взята задача (для справки)')
    )
    
    order = models.PositiveIntegerField(
        verbose_name=_('Порядковый номер'),
        default=0,
        help_text=_('Порядок отображения задачи в списке')
    )
    
    description = models.TextField(
        verbose_name=_('Описание задачи'),
        help_text=_('Подробное описание задачи и требований к выполнению')
    )
    
    is_completed = models.BooleanField(
        verbose_name=_('Выполнена'),
        default=False,
        help_text=_('Отметка о выполнении задачи')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Задача {self.order}: {self.description[:50]}..."
    
    def clean(self):
        """Валидация задачи."""
        # Проверка, что source_specification относится к тому же НИОКР
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
        indexes = [
            models.Index(fields=['rnd', 'is_completed']),
        ]


@receiver(pre_save, sender=Contract)
def track_contract_status_change(sender, instance, **kwargs):
    """
    Отслеживаем изменение статуса договора.
    """
    if instance.pk:
        try:
            old_instance = Contract.objects.get(pk=instance.pk)
            instance._status_changed = (old_instance.status != instance.status)
        except Contract.DoesNotExist:
            instance._status_changed = False
    else:
        instance._status_changed = False


@receiver(post_save, sender=Contract)
def update_rnd_status_on_contract_status_change(sender, instance, created, **kwargs):
    """
    Обновляем статусы НИОКР только при изменении статуса договора.
    """
    # Проверяем, является ли договор основным и изменился ли его статус
    if instance.is_main_contract and hasattr(instance, '_status_changed') and instance._status_changed:
        # Массовое обновление статусов НИОКР через bulk_update для эффективности
        rnd_works = RnD.objects.filter(contract=instance)
        
        status_mapping = {
            'active': 'in_progress',
            'suspended': 'suspended',
            'completed': 'completed',
            'terminated': 'contract_terminated',
        }
        
        new_status = status_mapping.get(instance.status, 'in_progress')
        
        # Подготавливаем объекты для обновления
        rnds_to_update = []
        for rnd in rnd_works:
            if rnd.status != new_status:
                rnd.status = new_status
                rnd.last_contract_status = instance.status
                rnds_to_update.append(rnd)
        
        # Массовое обновление
        if rnds_to_update:
            RnD.objects.bulk_update(
                rnds_to_update, 
                ['status', 'last_contract_status', 'updated_at']
            )
            
            # Отправляем сигналы post_save для обновленных объектов
            for rnd in rnds_to_update:
                post_save.send(
                    sender=RnD,
                    instance=rnd,
                    created=False,
                    update_fields=['status', 'last_contract_status']
                )


def update_all_rnd_statuses_for_contract(contract_id):
    """
    Вспомогательная функция для принудительного обновления статусов НИОКР.
    Может быть использована в админке или через команду.
    """
    try:
        contract = Contract.objects.get(pk=contract_id, is_main_contract=True)
        
        # Используем F-выражения для эффективного обновления
        status_mapping = {
            'active': 'in_progress',
            'suspended': 'suspended',
            'completed': 'completed',
            'terminated': 'contract_terminated',
        }
        
        new_status = status_mapping.get(contract.status, 'in_progress')
        
        # Обновляем все НИОКР для этого договора
        updated_count = RnD.objects.filter(contract=contract).update(
            status=new_status,
            last_contract_status=contract.status,
            updated_at=F('updated_at')
        )
        
        return updated_count
    except Contract.DoesNotExist:
        return 0