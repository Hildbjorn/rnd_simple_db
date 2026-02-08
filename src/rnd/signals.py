from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db.models import F
from .models import Contract, RnD


@receiver(pre_save, sender=Contract)
def track_contract_status_change(sender, instance, **kwargs):
    """Отслеживаем изменение статуса договора."""
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
    """Обновляем статусы НИОКР при изменении статуса договора."""
    if instance.is_main_contract and hasattr(instance, '_status_changed') and instance._status_changed:
        rnd_works = RnD.objects.filter(contract=instance)
        status_mapping = {
            'active': 'in_progress',
            'suspended': 'suspended',
            'completed': 'completed',
            'terminated': 'contract_terminated',
        }
        new_status = status_mapping.get(instance.status, 'in_progress')
        
        rnds_to_update = []
        for rnd in rnd_works:
            if rnd.status != new_status:
                rnd.status = new_status
                rnd.last_contract_status = instance.status
                rnds_to_update.append(rnd)
        
        if rnds_to_update:
            RnD.objects.bulk_update(
                rnds_to_update, 
                ['status', 'last_contract_status', 'updated_at']
            )


@receiver(post_save, sender=Contract)
def ensure_main_contract_integrity(sender, instance, created, **kwargs):
    """Гарантируем целостность ссылок main_contract после сохранения."""
    if not instance.type.is_supplementary and instance.main_contract != instance:
        instance.main_contract = instance
        instance.save(update_fields=['main_contract'])