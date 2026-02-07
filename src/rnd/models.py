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
                                            verbose_name=_('Тип НИОКР'),
                                            null=False,
                                            blank=False,
                                            help_text=_('Тип НИОКР')
                                            )
    
    short_name = models.CharField(max_length=255,
                                            verbose_name=_('Тип НИОКР (полностью)'),
                                            null=False,
                                            blank=False,
                                            help_text=_('Тип НИОКР (полностью)')
                                            )
    
    description = models.TextField(verbose_name='Краткое описание',
                                                        null=True,
                                                        blank=True
                                                        )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Тип НИОКР')
        verbose_name_plural = _('Типы НИОКР')
        ordering = ['id']


class TechnicalSpecification(models.Model):
    """
    Модель для хранения технических заданий и их изменений.
    """
    
    type = models.ForeignKey(RnDType,
                                            on_delete=models.CASCADE,
                                            verbose_name='Тип НИОКР',
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
    
    content = models.TextField(verbose_name=_('Содержание технического задания'),
                                                    null=True,
                                                    blank=True,
                                                    help_text=_('Полное содержание технического задания')
                                                    )
    
    created_at = models.DateField(verbose_name=_('Дата создания'),
                                                    auto_now_add=True)
    
    updated_at = models.DateField(verbose_name=_('Дата обновления'),
                                                    auto_now=True)
    
    contract = models.ForeignKey(Contract,
                                                on_delete=models.CASCADE,
                                                verbose_name=_('ГК / договор'),
                                                null=True,
                                                related_name='technical_specifications',
                                                help_text=_('Договор, к которому относится техническое задание'))
    
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


class RnD(models.Model):
    """
    Основная модель для хранения информации 
    о научно-исследовательских 
    и опытно-конструкторских работах (НИОКР).
    """
    
    technical_specification = models.ForeignKey(TechnicalSpecification,
                                                                on_delete=models.CASCADE,
                                                                verbose_name='Техническое задание',
                                                                null=True,
                                                                related_name='rnd_specifications',
                                                                help_text=_('Техническое задание, на основе которого выполняется НИОКР'))

    def __str__(self):
        if self.technical_specification:
            return f'{self.technical_specification.type if self.technical_specification.type else 'Без типа'} шифр "{self.technical_specification.code}"'
        return f"НИОКР №{self.id}"

    class Meta:
        verbose_name = _('НИОКР')
        verbose_name_plural = _('НИОКР')
        ordering = ['technical_specification__code']