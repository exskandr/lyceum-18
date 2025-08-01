from .models import NavbarSubItem # Переконайтеся, що шлях до models.py правильний

def navbar_items(request):
    """
    Контекстний процесор, який додає дані для навігаційного меню в контекст шаблону.
    """
    sub_items = NavbarSubItem.objects.all().order_by('order')
    navbar_data = {}
    for category_key, category_label in NavbarSubItem.MAIN_CATEGORIES:
        navbar_data[category_key] = {
            'label': category_label,
            'sub_items': sub_items.filter(category=category_key),
        }
    return {'navbar': navbar_data} # 'navbar' - це назва змінної, яка буде доступна в шаблонах
