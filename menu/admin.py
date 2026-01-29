from django.contrib import admin
from .models import Category, MealTime, Dish

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(MealTime)
class MealTimeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'get_meal_times', 'price', 'calories', 'created_at']
    list_filter = ['category', 'meal_times', 'created_at']
    search_fields = ['name']
    filter_horizontal = ['meal_times']
    
    def get_meal_times(self, obj):
        return ", ".join([mt.name for mt in obj.meal_times.all()])
    get_meal_times.short_description = '供應時段'