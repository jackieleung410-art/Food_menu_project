#!/usr/bin/env python3
import os
import sys

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_project.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from menu.models import Dish, Category, MealTime

print("資料庫檢查報告")
print("=" * 50)

# 檢查總數
total_dishes = Dish.objects.count()
total_categories = Category.objects.count()
total_meal_times = MealTime.objects.count()

print(f"菜餚總數: {total_dishes}")
print(f"食材類別總數: {total_categories}")
print(f"供應時段總數: {total_meal_times}")

# 檢查資料完整性
print("\n詳細資料:")
print("-" * 80)
print(f"{'菜名':<20} {'類別':<10} {'價格':<8} {'熱量':<10} {'供應時段':<20}")
print("-" * 80)

for dish in Dish.objects.all():
    meal_times = ', '.join([mt.name for mt in dish.meal_times.all()])
    print(f"{dish.name[:18]:<20} {dish.category.name[:8]:<10} ¥{dish.price:<7} {dish.calories:<10} {meal_times[:18]:<20}")

# 檢查是否有問題
print("\n檢查結果:")
if total_dishes == 20:
    print("✓ 菜餚數量正確 (20筆)")
else:
    print(f"✗ 菜餚數量不正確: {total_dishes} 筆，應為 20 筆")

if total_categories == 5:
    print("✓ 食材類別數量正確 (5種)")
else:
    print(f"✗ 食材類別數量不正確: {total_categories} 種，應為 5 種")

if total_meal_times == 3:
    print("✓ 供應時段數量正確 (3種)")
else:
    print(f"✗ 供應時段數量不正確: {total_meal_times} 種，應為 3 種")