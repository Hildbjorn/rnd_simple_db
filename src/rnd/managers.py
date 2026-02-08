from django.db import models
from django.db.models import Count, Q


class ContractManager(models.Manager):
    """Кастомный менеджер для контрактов."""
    
    def with_related_counts(self):
        return self.get_queryset().annotate(
            related_docs_count=Count('related_documents')
        )
    
    def main_contracts(self):
        return self.filter(type__is_supplementary=False)
    
    def supplementary_agreements(self):
        return self.filter(type__is_supplementary=True)


class RnDManager(models.Manager):
    """Кастомный менеджер для НИОКР."""
    
    def with_optimized_relations(self):
        return self.get_queryset().select_related(
            'contract', 'type', 'contract__type'
        )
    
    def active(self):
        return self.filter(
            Q(status='in_progress') | Q(status='suspended')
        )