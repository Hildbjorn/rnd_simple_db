"""
Модели для системы управления контрактами и НИОКР.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class ContractType(models.Model):
    """
    Типы договоров.
    
    Attributes:
        name (str): Полное название типа договора
        short_name (str): Краткое название типа договора
        description (str): Описание типа договора
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
    
    description = models.TextField(
        verbose_name=_('Краткое описание'),
        blank=True,
        null=True,
        help_text=_('Подробное описание типа договора')
    )
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Валидация данных модели."""
        if self.short_name and len(self.short_name) > 100:
            raise ValidationError({
                'short_name': _('Краткое название не должно превышать 100 символов')
            })
    
    class Meta:
        verbose_name = _('Тип договора')
        verbose_name_plural = _('Типы договоров')
        ordering = ['short_name']
        indexes = [
            models.Index(fields=['short_name']),
        ]


class Contract(models.Model):
    """
    Основная модель для хранения информации о контрактах.
    
    Attributes:
        type (ContractType): Тип контракта
        number (str): Номер контракта
        created_at (datetime): Дата создания записи
        updated_at (datetime): Дата последнего обновления
    """
    
    type = models.ForeignKey(
        ContractType,
        on_delete=models.PROTECT,
        verbose_name=_('Тип контракта'),
        related_name='contracts',
        help_text=_('Тип контракта (государственный, договор и т.д.)')
    )
    
    number = models.CharField(
        max_length=255,
        verbose_name=_('Номер контракта'),
        unique=True,  # Добавлена уникальность
        help_text=_('Уникальный номер контракта/договора')
    )
    
    created_at = models.DateTimeField(
        verbose_name=_('Дата создания'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        verbose_name=_('Дата обновления'),
        auto_now=True
    )
    
    def __str__(self):
        return f"{self.number} ({self.type.short_name})"
    
    def clean(self):
        """Валидация номера контракта."""
        if not self.number or not self.number.strip():
            raise ValidationError({
                'number': _('Номер контракта обязателен для заполнения')
            })
    
    class Meta:
        verbose_name = _('Контракт')
        verbose_name_plural = _('Контракты')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['type']),
        ]


class RnDType(models.Model):
    """
    Типы научно-исследовательских и опытно-конструкторских работ.
    
    Attributes:
        name (str): Название типа НИОКР
        short_name (str): Краткое название
        description (str): Описание типа работ
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


class TechnicalSpecification(models.Model):
    """
    Техническое задание для НИОКР.
    
    Attributes:
        contract (Contract): Связанный контракт
        type (RnDType): Тип работ
        code (str): Шифр работы
        title (str): Тема работы
        purpose (str): Цель работы
        is_active (bool): Актуальность версии
        previous_version (TechnicalSpecification): Предыдущая версия
    """
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Контракт'),
        related_name='technical_specifications',
        help_text=_('Контракт, к которому относится техническое задание')
    )
    
    type = models.ForeignKey(
        RnDType,
        on_delete=models.PROTECT,
        verbose_name=_('Тип работ'),
        related_name='technical_specifications',
        help_text=_('Тип научно-исследовательских работ')
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
        null=True,
        blank=True,
        help_text=_('Основные цели и задачи работы')
    )
    
    is_active = models.BooleanField(
        verbose_name=_('Актуальная версия'),
        default=True,
        help_text=_('Отметка актуальности данной версии ТЗ')
    )
    
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        verbose_name=_('Предыдущая версия'),
        null=True,
        blank=True,
        related_name='next_versions',
        help_text=_('Связь с предыдущей версией технического задания')
    )
    
    created_at = models.DateTimeField(
        verbose_name=_('Дата создания'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        verbose_name=_('Дата обновления'),
        auto_now=True
    )
    
    def __str__(self):
        return f"{self.code}: {self.title}"
    
    def clean(self):
        """Валидация технического задания."""
        if self.is_active and self.previous_version:
            # Деактивируем предыдущую активную версию
            TechnicalSpecification.objects.filter(
                contract=self.contract,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
        
        # Проверяем уникальность активного ТЗ для контракта
        if self.is_active and self.contract:
            existing_active = TechnicalSpecification.objects.filter(
                contract=self.contract,
                is_active=True
            ).exclude(id=self.id).exists()
            
            if existing_active:
                raise ValidationError({
                    'is_active': _('Для одного контракта может быть только одно активное ТЗ')
                })
    
    def save(self, *args, **kwargs):
        """Переопределение save для автоматической валидации."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('Техническое задание')
        verbose_name_plural = _('Технические задания')
        ordering = ['contract', '-is_active', 'code']
        unique_together = [['contract', 'code']]
        indexes = [
            models.Index(fields=['contract', 'is_active']),
            models.Index(fields=['code']),
        ]


class RnDTask(models.Model):
    """
    Задача в рамках технического задания.
    
    Attributes:
        technical_specification (TechnicalSpecification): Родительское ТЗ
        order (int): Порядковый номер задачи
        description (str): Описание задачи
        is_completed (bool): Статус выполнения
    """
    
    technical_specification = models.ForeignKey(
        TechnicalSpecification,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Техническое задание'),
        related_name='tasks',
        help_text=_('Техническое задание, к которому относится задача')
    )
    
    order = models.PositiveIntegerField(
        verbose_name=_('Порядковый номер'),
        default=0,
        help_text=_('Порядок отображения задачи в списке')
    )
    
    description = models.TextField(
        verbose_name=_('Описание задачи'),
        null=True,
        blank=True,
        help_text=_('Подробное описание задачи и требований к выполнению')
    )
    
    is_completed = models.BooleanField(
        verbose_name=_('Выполнена'),
        default=False,
        help_text=_('Отметка о выполнении задачи')
    )
    
    created_at = models.DateTimeField(
        verbose_name=_('Дата создания'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        verbose_name=_('Дата обновления'),
        auto_now=True
    )
    
    def __str__(self):
        return f"Задача {self.order}: {self.description[:50]}..."
    
    class Meta:
        verbose_name = _('Задача НИОКР')
        verbose_name_plural = _('Задачи НИОКР')
        ordering = ['technical_specification', 'order']
        unique_together = [['technical_specification', 'order']]
        indexes = [
            models.Index(fields=['technical_specification', 'is_completed']),
        ]


class RnD(models.Model):
    """
    Научно-исследовательская или опытно-конструкторская работа.
    
    Attributes:
        technical_specification (TechnicalSpecification): Активное ТЗ
        status (str): Статус выполнения работы
    """
    
    STATUS_CHOICES = [
        ('draft', _('Черновик')),
        ('in_progress', _('В работе')),
        ('completed', _('Завершена')),
        ('cancelled', _('Отменена')),
    ]
    
    technical_specification = models.OneToOneField(  # Изменено с ForeignKey на OneToOneField
        TechnicalSpecification,
        on_delete=models.PROTECT,  # Защита от удаления активного ТЗ
        verbose_name=_('Активное техническое задание'),
        related_name='rnd',
        help_text=_('Актуальная версия технического задания для работы'),
        limit_choices_to={'is_active': True}  # Ограничиваем выбор только активными ТЗ
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Статус'),
        help_text=_('Текущий статус выполнения НИОКР')
    )
    
    created_at = models.DateTimeField(
        verbose_name=_('Дата создания'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        verbose_name=_('Дата обновления'),
        auto_now=True
    )
    
    def __str__(self):
        contract = self.technical_specification.contract
        return f"НИОКР: {contract.number} ({self.get_status_display()})"
    
    @property
    def contract(self):
        """Свойство для доступа к контракту через ТЗ."""
        return self.technical_specification.contract
    
    @property
    def contract_number(self):
        """Номер контракта."""
        return self.technical_specification.contract.number
    
    @property
    def code(self):
        """Шифр работы."""
        return self.technical_specification.code
    
    @property
    def title(self):
        """Тема работы."""
        return self.technical_specification.title
    
    @property
    def type(self):
        """Тип работ."""
        return self.technical_specification.type
    
    def clean(self):
        """Валидация НИОКР."""
        # Проверяем, что ТЗ активно
        if not self.technical_specification.is_active:
            raise ValidationError({
                'technical_specification': _('Можно выбрать только активное техническое задание')
            })
    
    class Meta:
        verbose_name = _('НИОКР')
        verbose_name_plural = _('НИОКР')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['technical_specification']),
        ]