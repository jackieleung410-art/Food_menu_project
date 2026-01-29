from django.db import models

class Category(models.Model):
    """食材類別"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class MealTime(models.Model):
    """供應時段"""
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Dish(models.Model):
    """菜餚"""
    name = models.CharField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='dishes')
    meal_times = models.ManyToManyField(MealTime, related_name='dishes')
    price = models.DecimalField(max_digits=6, decimal_places=2)
    calories = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Dishes"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - ¥{self.price}"