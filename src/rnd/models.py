from django.db import models
from django.utils.translation import gettext_lazy as _


class ContractType(models.Model):
    """
    Типы договоров.
    """
    
    name = models.CharField(max_length=255,
                                            verbose_name=_('Тип договора (полностью)'),
                                            null=False,
                                            blank=False,
                                            help_text=_('Тип договора (полностью)')
                                            )
    
    short_name = models.CharField(max_length=255,
                                            verbose_name=_('Тип договора (кратко)'),
                                            null=False,
                                            blank=False,
                                            help_text=_('Тип договора (кратко)')
                                            )
    
    description = models.TextField(verbose_name='Краткое описание',
                                                        null=True,
                                                        blank=True
                                                        )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Тип договора')
        verbose_name_plural = _('Типы договоров')
        ordering = ['id']


class Contract(models.Model):
    """
    Основная модель для хранения информации о государственных контрактах, 
    договорах с соисполнителями и дополнительных соглашениях к ним.
    """
    
    type = models.ForeignKey(ContractType,
                                            on_delete=models.CASCADE,
                                            verbose_name='Тип ГК / договора',
                                            null=True,
                                            related_name='contract_type')
    
    number = models.CharField(max_length=255,
                                            verbose_name=_('Номер ГК / договора'),
                                            null=True,
                                            blank=True,
                                            help_text=_('Номер ГК / договора')
                                            )
    
    def __str__(self):
        return self.number
    
    class Meta:
        verbose_name = _('Государственный контракт / Договор')
        verbose_name_plural = _('Государственные контракты / Договоры')
        ordering = ['number']


class RnDType(models.Model):
    """
    Типы НИОКР согласно классификации.
    """
    
    name = models.CharField(max_length=255,
                                            verbose_name=_('Вид работы'),
                                            null=False,
                                            blank=False,
                                            help_text=_('Вид работы')
                                            )
    
    short_name = models.CharField(max_length=255,
                                            verbose_name=_('Вид работы (полностью)'),
                                            null=False,
                                            blank=False,
                                            help_text=_('Вид работы (полностью)')
                                            )
    
    description = models.TextField(verbose_name='Краткое описание',
                                                        null=True,
                                                        blank=True
                                                        )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Вид работы')
        verbose_name_plural = _('Типы НИОКР')
        ordering = ['id']


class TechnicalSpecification(models.Model):
    """
    Модель для хранения технических заданий и их изменений.
    """
    
    contract = models.ForeignKey(Contract,
                                                on_delete=models.CASCADE,
                                                verbose_name=_('ГК / договор'),
                                                null=True,
                                                related_name='technical_specifications',
                                                help_text=_('Договор, к которому относится техническое задание'))
    
    type = models.ForeignKey(RnDType,
                                            on_delete=models.CASCADE,
                                            verbose_name='Вид работы',
                                            null=True,
                                            related_name='rnd_types')
    
    code = models.CharField(max_length=255,
                                            verbose_name=_('Шифр работы'),
                                            null=True,
                                            blank=True,
                                            help_text=_('Шифр работы в соответствии с государственным контрактом или договором')
                                            )
    
    title = models.CharField(max_length=500,
                                             verbose_name=_('Тема работы'),
                                             null=True,
                                             blank=True,
                                             help_text=_('Наименование темы работы в соответствии с государственным контрактом или договором')
                                             )
    
    purpose = models.TextField(verbose_name=_('Цель работы'),
                                                    null=True,
                                                    blank=True,
                                                    help_text=_('Основная цель работы')
                                                    )
    
    created_at = models.DateField(verbose_name=_('Дата создания'),
                                                    auto_now_add=True)
    
    updated_at = models.DateField(verbose_name=_('Дата обновления'),
                                                    auto_now=True)
    
    is_active = models.BooleanField(verbose_name=_('Актуальная версия'),
                                                        default=True,
                                                        help_text=_('Отметка, является ли эта версия актуальной'))
    
    previous_version = models.ForeignKey('self',
                                                            on_delete=models.SET_NULL,
                                                            verbose_name=_('Предыдущая версия'),
                                                            null=True,
                                                            blank=True,
                                                            related_name='next_versions',
                                                            help_text=_('Ссылка на предыдущую версию ТЗ'))
    
    def __str__(self):
        return f'{self.type} шифр "{self.code}"'
    
    class Meta:
        verbose_name = _('Техническое задание')
        verbose_name_plural = _('Технические задания')
        ordering = ['code', '-created_at']


class RnDTask(models.Model):
    """
    Модель для хранения задач работы в рамках технического задания.
    """
    
    order = models.PositiveIntegerField(verbose_name=_('Порядковый номер'),
                                                            default=0,
                                                            help_text=_('Порядок отображения задачи'))
    
    technical_specification = models.ForeignKey(TechnicalSpecification,
                                                                on_delete=models.CASCADE,
                                                                verbose_name=_('Техническое задание'),
                                                                null=True,
                                                                related_name='work_tasks',
                                                                help_text=_('Техническое задание, к которому относится задача'))
    
    description = models.TextField(verbose_name=_('Описание задачи'),
                                                    null=False,
                                                    blank=False,
                                                    help_text=_('Подробное описание задачи')
                                                    )
    
    created_at = models.DateTimeField(verbose_name=_('Дата создания'),
                                                        auto_now_add=True)
    
    updated_at = models.DateTimeField(verbose_name=_('Дата обновления'),
                                                        auto_now=True)
    
    def __str__(self):
        if self.technical_specification:
            return f'Задача {self.order} для {self.technical_specification.code}'
        return f'Задача #{self.id}'
    
    class Meta:
        verbose_name = _('Задача работы')
        verbose_name_plural = _('Задачи работы')
        ordering = ['technical_specification', 'order']
        unique_together = ['technical_specification', 'order']


class RnD(models.Model):
    """
    Основная модель для хранения информации 
    о научно-исследовательских 
    и опытно-конструкторских работах (НИОКР).
    """
    
    contract = models.ForeignKey(Contract,
                                                on_delete=models.CASCADE,
                                                verbose_name='ГК / договор',
                                                null=True,
                                                related_name='rnd_contracts',
                                                help_text=_('Договор, к которому относится НИОКР'))

    def __str__(self):
        if self.contract:
            # Получаем активное техническое задание для этого контракта
            active_tech_spec = self.contract.technical_specifications.filter(is_active=True).first()
            if active_tech_spec:
                return f'{active_tech_spec.type if active_tech_spec.type else "Без типа"} шифр "{active_tech_spec.code}" по контракту {self.contract.number}'
            return f"НИОКР по контракту {self.contract.number}"
        return f"НИОКР №{self.id}"

    class Meta:
        verbose_name = _('НИОКР')
        verbose_name_plural = _('НИОКР')
        ordering = ['contract__number']

    def get_active_technical_specification(self):
        """Возвращает активное техническое задание для этого НИОКР."""
        if self.contract:
            return self.contract.technical_specifications.filter(is_active=True).first()
        return None