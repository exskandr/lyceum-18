# core/templatetags/app_filters.py

from django import template
import logging

register = template.Library()


# @register.filter
# def get_item(dictionary, key):
#     """
#     Повертає значення елемента словника за заданим ключем.
#     Дозволяє використовувати dict|get_item:key в Django шаблонах.
#     """
#     return dictionary.get(key)


logger = logging.getLogger(__name__)


@register.filter
def get_item(dictionary, key):
    logger.debug(
        f"get_item called: dictionary={dictionary!r} (type={type(dictionary)}), key={key!r} (type={type(key)})")

    if dictionary is None:
        logger.error(f"get_item received None as dictionary for key={key}")
        return None  # or {}

    # Додаємо цю перевірку, щоб бути впевненими, що це Dict-подібний об'єкт
    if not hasattr(dictionary, 'get'):
        logger.error(f"get_item received non-dict-like object (type={type(dictionary)}) for key={key}")
        # Це означає, що dictionary НЕ є словником або defaultdict, і не має методу .get()
        return None  # Або поверніть виняток, якщо ви хочете, щоб це був справжній збій

    result = dictionary.get(key)
    logger.debug(f"get_item result for key={key}: {result!r} (type={type(result)})")
    return result


@register.filter
def mul(value, arg):
    """
    Помножує значення на аргумент.
    Використання: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return '' # Повертаємо порожню строку у випадку помилки, або 0, або None