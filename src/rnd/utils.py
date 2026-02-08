import os
import uuid
import hashlib
from django.utils import timezone


class UploadPathFactory:
    """
    Фабрика для генерации коротких путей загрузки файлов.
    Создает структуру: {rnd_uuid}/{type}/{yymmdd}/{short_uuid}.ext
    """
    
    @staticmethod
    def for_technical_specification(instance, filename):
        """Короткий путь для технических заданий."""
        file_uuid = uuid.uuid4().hex[:8]
        file_ext = os.path.splitext(filename)[1].lower()
        safe_filename = f"{file_uuid}{file_ext}"
        date_short = timezone.now().strftime('%y%m%d')
        rnd_uuid = UploadPathFactory._get_rnd_uuid_safe(instance)
        return os.path.join(rnd_uuid, 'tech_spec', date_short, safe_filename)
    
    @staticmethod
    def for_contract_document(instance, filename):
        """Короткий путь для сканов договоров."""
        file_uuid = uuid.uuid4().hex[:8]
        file_ext = os.path.splitext(filename)[1].lower()
        safe_filename = f"{file_uuid}{file_ext}"
        date_short = timezone.now().strftime('%y%m%d')
        rnd_uuid = UploadPathFactory._get_contract_rnd_uuid(instance)
        return os.path.join(rnd_uuid, 'contracts', date_short, safe_filename)
    
    @staticmethod
    def _get_rnd_uuid_safe(instance):
        """Безопасное получение UUID НИОКР из instance."""
        try:
            if hasattr(instance, 'rnd') and instance.rnd:
                return str(instance.rnd.uuid)
            elif hasattr(instance, 'uuid') and instance.uuid:
                return str(instance.uuid)
        except Exception:
            pass
        return 'temp_' + uuid.uuid4().hex[:8]
    
    @staticmethod
    def _get_contract_rnd_uuid(instance):
        """Получаем UUID НИОКР для договора через связанные НИОКР."""
        try:
            if hasattr(instance, 'rnd_works'):
                rnd_work = instance.rnd_works.first()
                if rnd_work:
                    return str(rnd_work.uuid)
        except Exception:
            pass
        
        if hasattr(instance, 'number') and instance.number:
            hash_obj = hashlib.md5(instance.number.encode())
            return f"doc_{hash_obj.hexdigest()[:12]}"
        
        return 'temp_' + uuid.uuid4().hex[:8]