from django import template

register = template.Library()


@register.filter
def split(value, key):
    """
    Розділяє рядок за заданим роздільником.
    Використання: {{ value|split:',' }}
    """
    return value.split(key)


@register.filter
def get_item(dictionary, key):
    """
    Дозволяє доступ до елементів словника за допомогою змінної ключа в шаблоні.
    Використання: {{ dictionary|get_item:key_variable }}
    """
    return dictionary.get(key)
