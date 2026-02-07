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


class RnD(models.Model):
    """
    Основная модель для хранения информации 
    о научно-исследовательских и опытно-конструкторских работах (НИОКР).
    """
    
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
    
    type = models.ForeignKey(RnDType,
                                            on_delete=models.CASCADE,
                                            verbose_name='Тип НИОКР',
                                            null=True,
                                            related_name='rnd_type')
    
    contract = models.ForeignKey(Contract,
                                                on_delete=models.CASCADE,
                                                verbose_name='ГК / договор',
                                                null=True,
                                                related_name='rnd_contract')
    
    def __str__(self):
        return self.code
    
    class Meta:
        verbose_name = _('НИОКР')
        verbose_name_plural = _('НИОКР')
        ordering = ['code']