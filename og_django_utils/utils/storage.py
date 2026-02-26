from django.core.files.storage import storages
from django.utils.module_loading import import_string


def get_storage_class(import_path):
    """
    Get a storage class instance from a path string.

    This function replaces the deprecated django.core.files.storage.get_storage_class()
    which was removed in Django 5.1.

    Args:
        import_path: Either a storage alias (e.g., 'default', 'staticfiles') or
                    a dotted path to a storage class (e.g., 'django.core.files.storage.FileSystemStorage')

    Returns:
        Storage class (not instantiated)

    Examples:
        >>> storage_class = get_storage_class('default')
        >>> storage_class = get_storage_class('django.core.files.storage.FileSystemStorage')
    """
    if not isinstance(import_path, str):
        raise TypeError(f"import_path must be a string, got {type(import_path).__name__}")

    # If it looks like a dotted path (contains a dot), import it directly
    if "." in import_path:
        return import_string(import_path)

    # Otherwise, try as storage alias (e.g., 'default', 'staticfiles')
    try:
        storage_instance = storages[import_path]
        return storage_instance.__class__
    except KeyError:
        # If not found as alias, try importing anyway (edge case)
        return import_string(import_path)
