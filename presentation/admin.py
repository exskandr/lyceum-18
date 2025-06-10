from django.contrib import admin
from .models import News, NavbarSubItem, DynamicPage
from django.utils.html import format_html


@admin.register(DynamicPage)
class DynamicPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}  # Автоматично генерує slug із назви


@admin.register(NavbarSubItem)
class NavbarSubItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'url', 'order')
    list_editable = ('order', 'url')
    list_filter = ('category',)


# admin.site.register(News)
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['publish', 'show_main_image', 'title', 'slug', 'status']
    list_filter = ['status', 'created', 'publish', 'author']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']
    show_facets = admin.ShowFacets.ALWAYS

    def show_main_image(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="100" />', obj.main_image.url)
        return "No Image"

    show_main_image.short_description = 'Головне зображення'