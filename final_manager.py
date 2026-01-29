#!/usr/bin/env python3
"""
最終版資料管理工具 - 完整修正版 (包含修復價格功能)
"""

import os
import sys
import csv
import re
from datetime import datetime

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_project.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from menu.models import Dish, Category, MealTime

class FoodDataManager:
    def __init__(self):
        self.data = []
        self.original_csv_data = []  # 保存原始CSV數據以供修復使用
    
    def clean_text(self, text):
        """清理文字 - 修正包含 @ 符號"""
        if not text or str(text).lower() == 'nan':
            return ""
        
        text = str(text)
        # 移除特殊符號 - 包含 @ 符號
        text = re.sub(r'[#$%^&*()_+=\[\]{}|;:"<>?/~`@]', '', text)
        
        # 修正常見錯誤
        corrections = {
            '午餐晚餐': '午餐,晚餐',
            '早餐午餐': '早餐,午餐',
            '午餐 晚餐': '午餐,晚餐',
            '早餐 午餐': '早餐,午餐',
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # 移除多餘空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def process_price(self, price_str):
        """處理價格字串轉換為浮點數 - 修正版"""
        if not price_str:
            return 0.0
        
        try:
            # 清理字串
            price_str = str(price_str).strip()
            
            # 移除貨幣相關文字和符號
            replacements = ['元', '¥', '$', 'RMB', 'NTD', 'NT', 'USD']
            for rep in replacements:
                price_str = price_str.replace(rep, '')
            
            # 只保留數字、小數點和負號
            price_str = re.sub(r'[^\d.-]', '', price_str)
            
            # 如果是空字串，返回0
            if not price_str:
                return 0.0
            
            # 轉換為浮點數
            result = float(price_str)
            
            # 確保價格是合理的（不小於0）
            if result < 0:
                return 0.0
                
            return result
        except:
            return 0.0
    
    def process_calories(self, cal_str):
        """處理熱量字串轉換為整數 - 修正版"""
        if not cal_str:
            return 0
        
        try:
            # 清理字串
            cal_str = str(cal_str).strip()
            
            # 移除單位文字
            replacements = ['卡路里', '卡', 'cal', 'calories']
            for rep in replacements:
                cal_str = cal_str.replace(rep, '')
            
            # 只保留數字
            cal_str = re.sub(r'[^\d]', '', cal_str)
            
            # 如果是空字串，返回0
            if not cal_str:
                return 0
            
            # 轉換為整數
            result = int(cal_str)
            
            # 確保熱量是合理的（不小於0）
            if result < 0:
                return 0
                
            return result
        except:
            return 0
    
    def load_csv(self, file_path):
        """載入 CSV 檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.original_csv_data = []
                for row in reader:
                    cleaned_row = {}
                    for key, value in row.items():
                        cleaned_row[key] = self.clean_text(value)
                    self.original_csv_data.append(cleaned_row)
            
            self.data = self.original_csv_data.copy()  # 複製一份給其他方法使用
            
            print(f"✓ 成功載入 {len(self.data)} 筆資料")
            
            # 顯示載入的資料預覽
            if self.data and len(self.data) > 0:
                print("\n前3筆資料預覽:")
                for i, row in enumerate(self.data[:3]):
                    print(f"  第{i+1}筆: {row}")
            
            return True
        except Exception as e:
            print(f"✗ 載入失敗: {e}")
            return False
    
    def clean_data(self):
        """清理資料 - 修正價格處理"""
        if not self.data:
            print("沒有資料可清理")
            return False
        
        print("開始清理資料...")
        
        processed_data = []
        for row in self.data:
            try:
                # 檢查必要欄位
                dish_name = row.get('菜名') or row.get('菜名') or ''
                if not dish_name:
                    print(f"警告: 跳過缺少菜名的資料: {row}")
                    continue
                
                # 標準化欄位名稱
                standardized_row = {
                    '菜名': self.clean_text(row.get('菜名', '')),
                    '主要食材': self.clean_text(row.get('主要食材', row.get('主要食材', '未知'))),
                    '供應時段': self.clean_text(row.get('供應時段', row.get('供應時段', ''))),
                    '價格(元)': self.clean_text(row.get('價格(元)', row.get('價格', '0'))),
                    '熱量(卡路里)': self.clean_text(row.get('熱量(卡路里)', row.get('熱量', '0'))),
                }
                
                # 處理供應時段分割
                times_str = standardized_row['供應時段']
                if times_str:
                    times_list = [t.strip() for t in re.split(r'[,，\s]+', times_str) if t.strip()]
                    standardized_row['供應時段列表'] = times_list
                else:
                    standardized_row['供應時段列表'] = []
                
                # 處理價格轉換 - 使用修正的方法
                price_str = standardized_row['價格(元)']
                standardized_row['價格_數值'] = self.process_price(price_str)
                
                # 處理熱量轉換 - 使用修正的方法
                cal_str = standardized_row['熱量(卡路里)']
                standardized_row['熱量_數值'] = self.process_calories(cal_str)
                
                # 記錄原始值以供除錯
                standardized_row['原始價格'] = price_str
                standardized_row['原始熱量'] = cal_str
                
                processed_data.append(standardized_row)
                
                # 顯示有問題的轉換
                if standardized_row['價格_數值'] == 0 and price_str and price_str != '0':
                    print(f"  警告: 價格轉換可能失敗 '{price_str}' -> 0")
                
            except Exception as e:
                print(f"清理資料時發生錯誤 (資料: {row}): {e}")
        
        self.data = processed_data
        print(f"✓ 資料清理完成，有效資料: {len(self.data)} 筆")
        
        # 顯示清理後的資料預覽
        if self.data and len(self.data) > 0:
            print("\n清理後前3筆資料:")
            for i, row in enumerate(self.data[:3]):
                print(f"  第{i+1}筆: {row}")
        
        return True
    
    def import_to_database(self):
        """匯入到資料庫 - 修正版"""
        if not self.data:
            print("沒有資料可匯入")
            return False
        
        success = 0
        errors = []
        
        print("開始匯入到資料庫...")
        
        # 先建立一個菜名到資料的映射（使用清理後的菜名）
        dish_name_to_data = {}
        for row in self.data:
            cleaned_name = self.clean_text(row.get('菜名', ''))
            if cleaned_name:
                dish_name_to_data[cleaned_name] = row
        
        print(f"可用的菜品資料: {len(dish_name_to_data)} 筆")
        
        for cleaned_name, row in dish_name_to_data.items():
            try:
                category_name = self.clean_text(row.get('主要食材', '未知'))
                price = row.get('價格_數值', 0.0)
                calories = row.get('熱量_數值', 0)
                meal_times_str = row.get('供應時段', '')
                meal_times_list = row.get('供應時段列表', [])
                
                # 顯示除錯資訊（如果有問題）
                if price == 0:
                    print(f"  注意: {cleaned_name} 價格為0 (原始: {row.get('原始價格', 'N/A')})")
                
                # 取得或創建食材類別
                category, _ = Category.objects.get_or_create(name=category_name)
                
                # 創建或更新菜餚
                dish, created = Dish.objects.update_or_create(
                    name=cleaned_name,
                    defaults={
                        'category': category,
                        'price': price,
                        'calories': calories,
                    }
                )
                
                # 設定供應時段
                meal_time_objects = []
                for time_name in meal_times_list:
                    meal_time, _ = MealTime.objects.get_or_create(name=time_name)
                    meal_time_objects.append(meal_time)
                
                dish.meal_times.set(meal_time_objects)
                
                success += 1
                if created:
                    print(f"  ✓ 新增: {cleaned_name} (¥{price}, {calories}卡)")
                else:
                    print(f"  ✓ 更新: {cleaned_name} (¥{price}, {calories}卡)")
                
            except Exception as e:
                errors.append(f"{cleaned_name}: {e}")
        
        print(f"\n匯入完成! 成功: {success}, 失敗: {len(errors)}")
        if errors:
            print("錯誤清單（前5個）:")
            for error in errors[:5]:
                print(f"  - {error}")
        
        return success > 0
    
    def fix_zero_prices(self):
        """修復價格為0的菜品"""
        if not self.original_csv_data:
            print("警告: 請先載入CSV數據")
            return False
        
        zero_price_dishes = Dish.objects.filter(price=0)
        print(f"找到 {zero_price_dishes.count()} 個價格為0的菜品")
        
        if zero_price_dishes.count() == 0:
            print("沒有需要修復的菜品")
            return True
        
        fixed_count = 0
        
        for dish in zero_price_dishes:
            # 在CSV數據中尋找匹配的菜品
            for csv_row in self.original_csv_data:
                csv_dish_name = self.clean_text(csv_row.get('菜名', ''))
                
                if csv_dish_name == dish.name:
                    # 找到匹配的菜品，修復價格和熱量
                    price_str = csv_row.get('價格(元)', csv_row.get('價格', '0'))
                    cal_str = csv_row.get('熱量(卡路里)', csv_row.get('熱量', '0'))
                    
                    price = self.process_price(price_str)
                    calories = self.process_calories(cal_str)
                    
                    if price > 0:  # 只有當找到有效價格時才更新
                        dish.price = price
                        dish.calories = calories
                        dish.save()
                        
                        # 也更新食材類別和供應時段
                        category_name = self.clean_text(csv_row.get('主要食材', '未知'))
                        if category_name:
                            category, _ = Category.objects.get_or_create(name=category_name)
                            dish.category = category
                        
                        # 更新供應時段
                        meal_times_str = csv_row.get('供應時段', '')
                        if meal_times_str:
                            times_list = [t.strip() for t in re.split(r'[,，\s]+', meal_times_str) if t.strip()]
                            meal_time_objects = []
                            for time_name in times_list:
                                meal_time, _ = MealTime.objects.get_or_create(name=time_name)
                                meal_time_objects.append(meal_time)
                            dish.meal_times.set(meal_time_objects)
                        
                        dish.save()
                        
                        print(f"  ✓ 修復: {dish.name} -> ¥{price}, {calories}卡")
                        fixed_count += 1
                    break  # 找到匹配就跳出循環
        
        print(f"\n修復完成! 修復了 {fixed_count} 個菜品的價格")
        
        # 檢查是否還有價格為0的菜品
        remaining_zero = Dish.objects.filter(price=0).count()
        if remaining_zero > 0:
            print(f"仍有 {remaining_zero} 個菜品價格為0:")
            for dish in Dish.objects.filter(price=0)[:10]:  # 只顯示前10個
                print(f"  - {dish.name}")
            if remaining_zero > 10:
                print(f"  ... 還有 {remaining_zero - 10} 個")
        
        return fixed_count > 0
    
    def fix_all_prices_from_csv(self):
        """從CSV文件修復所有菜品的價格（強制更新）"""
        if not self.original_csv_data:
            print("警告: 請先載入CSV數據")
            return False
        
        print("開始從CSV修復所有菜品價格...")
        
        fixed_count = 0
        total_dishes = Dish.objects.count()
        
        for dish in Dish.objects.all():
            # 在CSV數據中尋找匹配的菜品
            for csv_row in self.original_csv_data:
                csv_dish_name = self.clean_text(csv_row.get('菜名', ''))
                
                if csv_dish_name == dish.name:
                    # 找到匹配的菜品，更新價格和熱量
                    price_str = csv_row.get('價格(元)', csv_row.get('價格', '0'))
                    cal_str = csv_row.get('熱量(卡路里)', csv_row.get('熱量', '0'))
                    
                    price = self.process_price(price_str)
                    calories = self.process_calories(cal_str)
                    
                    # 更新數據庫記錄
                    dish.price = price
                    dish.calories = calories
                    
                    # 更新食材類別
                    category_name = self.clean_text(csv_row.get('主要食材', '未知'))
                    if category_name:
                        category, _ = Category.objects.get_or_create(name=category_name)
                        dish.category = category
                    
                    # 更新供應時段
                    meal_times_str = csv_row.get('供應時段', '')
                    if meal_times_str:
                        times_list = [t.strip() for t in re.split(r'[,，\s]+', meal_times_str) if t.strip()]
                        meal_time_objects = []
                        for time_name in times_list:
                            meal_time, _ = MealTime.objects.get_or_create(name=time_name)
                            meal_time_objects.append(meal_time)
                        dish.meal_times.set(meal_time_objects)
                    
                    dish.save()
                    
                    print(f"  ✓ 更新: {dish.name} -> ¥{price}, {calories}卡")
                    fixed_count += 1
                    break  # 找到匹配就跳出循環
        
        print(f"\n修復完成! 更新了 {fixed_count}/{total_dishes} 個菜品的價格")
        
        # 顯示未找到的菜品
        if fixed_count < total_dishes:
            print(f"有 {total_dishes - fixed_count} 個菜品在CSV中找不到:")
            all_dish_names = set(dish.name for dish in Dish.objects.all())
            csv_dish_names = set(self.clean_text(row.get('菜名', '')) for row in self.original_csv_data)
            missing_dishes = all_dish_names - csv_dish_names
            
            for dish_name in list(missing_dishes)[:10]:  # 只顯示前10個
                print(f"  - {dish_name}")
            if len(missing_dishes) > 10:
                print(f"  ... 還有 {len(missing_dishes) - 10} 個")
        
        return True
    
    def export_to_csv(self, file_path=None):
        """從資料庫匯出到 CSV"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"menu_export_{timestamp}.csv"
        
        try:
            dishes = Dish.objects.all().select_related('category').prefetch_related('meal_times')
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 寫入標題行（包含 BOM 用於 Excel 兼容）
                f.write('\ufeff')
                writer.writerow(['菜名', '主要食材', '供應時段', '價格(元)', '熱量(卡路里)'])
                
                for dish in dishes:
                    meal_times = ','.join([mt.name for mt in dish.meal_times.all()])
                    writer.writerow([dish.name, dish.category.name, meal_times, dish.price, dish.calories])
            
            print(f"✓ 成功匯出 {dishes.count()} 筆資料到 {file_path}")
            return True
            
        except Exception as e:
            print(f"✗ 匯出失敗: {e}")
            return False
    
    def list_dishes(self, limit=None):
        """列出菜餚"""
        if limit:
            dishes = Dish.objects.all().select_related('category').prefetch_related('meal_times')[:limit]
        else:
            dishes = Dish.objects.all().select_related('category').prefetch_related('meal_times')
        
        print(f"\n{'菜名':<20} {'主要食材':<10} {'價格':<10} {'熱量':<10} {'供應時段':<15}")
        print("=" * 70)
        
        zero_price_count = 0
        
        for dish in dishes:
            meal_times = ','.join([mt.name for mt in dish.meal_times.all()])
            price_display = f"¥{dish.price:.2f}"
            
            # 檢查價格是否為0
            if dish.price == 0:
                price_display = f"¥{dish.price:.2f}⚠️"
                zero_price_count += 1
            
            print(f"{dish.name[:18]:<20} {dish.category.name[:8]:<10} {price_display:<10} {dish.calories:<10} {meal_times[:14]:<15}")
        
        print(f"\n總計: {Dish.objects.count()} 筆記錄")
        if zero_price_count > 0:
            print(f"⚠️ 警告: 有 {zero_price_count} 個菜品價格為0")
    
    def delete_all_data(self):
        """刪除所有資料"""
        confirm = input("確定要刪除所有資料嗎？(yes/no): ")
        if confirm.lower() == 'yes':
            Dish.objects.all().delete()
            Category.objects.all().delete()
            MealTime.objects.all().delete()
            print("✓ 所有資料已刪除")
            return True
        else:
            print("✗ 取消刪除")
            return False
    
    def run_full_import(self, file_path):
        """執行完整匯入流程"""
        print("開始完整匯入流程...")
        print("=" * 50)
        
        if not self.load_csv(file_path):
            return False
        
        if not self.clean_data():
            return False
        
        self.import_to_database()
        print("=" * 50)
        print("完整匯入流程完成")
    
    def reload_and_fix_all(self):
        """重新載入並修復所有數據"""
        print("重新載入並修復所有數據...")
        
        # 先刪除所有現有數據
        self.delete_all_data()
        
        # 載入第一個CSV文件
        print("\n1. 載入 sample_clean.csv...")
        if not self.load_csv("sample_clean.csv"):
            print("載入 sample_clean.csv 失敗")
            return False
        
        self.clean_data()
        self.import_to_database()
        
        # 載入第二個CSV文件
        print("\n2. 載入 sample_data.csv...")
        if not self.load_csv("sample_data.csv"):
            print("載入 sample_data.csv 失敗")
            return False
        
        self.clean_data()
        self.import_to_database()
        
        # 執行強制修復
        print("\n3. 執行強制修復...")
        self.fix_all_prices_from_csv()
        
        print("\n" + "=" * 50)
        print("重新載入並修復完成!")
        return True

def main():
    """主程式"""
    manager = FoodDataManager()
    
    while True:
        print("\n" + "="*60)
        print("食物菜單資料管理系統 (完整修正版)")
        print("="*60)
        print("1. 載入 CSV 檔案")
        print("2. 清理資料")
        print("3. 匯入到資料庫")
        print("4. 從資料庫匯出到 CSV")
        print("5. 列出所有菜餚")
        print("6. 刪除所有資料")
        print("7. 執行完整匯入流程")
        print("8. 檢查資料庫狀態")
        print("9. 修復價格為0的菜品")
        print("10. 從CSV強制修復所有價格")
        print("11. 重新載入並修復所有數據")
        print("12. 離開")
        print("="*60)
        
        try:
            choice = input("請選擇操作 (1-12): ").strip()
            
            if choice == '1':
                file_path = input("請輸入 CSV 檔案路徑: ").strip()
                manager.load_csv(file_path)
            
            elif choice == '2':
                manager.clean_data()
            
            elif choice == '3':
                manager.import_to_database()
            
            elif choice == '4':
                default_file = f"menu_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                file_path = input(f"請輸入匯出檔案路徑 (直接按 Enter 使用 {default_file}): ").strip()
                if not file_path:
                    file_path = default_file
                manager.export_to_csv(file_path)
            
            elif choice == '5':
                limit_input = input("顯示筆數 (直接按 Enter 顯示全部): ").strip()
                if limit_input:
                    try:
                        limit = int(limit_input)
                        manager.list_dishes(limit)
                    except:
                        print("輸入無效，顯示全部")
                        manager.list_dishes()
                else:
                    manager.list_dishes()
            
            elif choice == '6':
                manager.delete_all_data()
            
            elif choice == '7':
                file_path = input("請輸入 CSV 檔案路徑: ").strip()
                manager.run_full_import(file_path)
            
            elif choice == '8':
                print(f"\n資料庫狀態:")
                print(f"  • 菜餚數量: {Dish.objects.count()}")
                print(f"  • 食材類別: {Category.objects.count()}")
                print(f"  • 供應時段: {MealTime.objects.count()}")
                
                # 檢查價格為0的菜餚
                zero_price = Dish.objects.filter(price=0).count()
                if zero_price > 0:
                    print(f"  • 價格為0的菜餚: {zero_price} (可能有問題)")
                    print("  前5個價格為0的菜餚:")
                    for dish in Dish.objects.filter(price=0)[:5]:
                        print(f"    - {dish.name}")
                
                categories = Category.objects.all()
                print(f"\n食材類別清單:")
                for cat in categories:
                    dish_count = Dish.objects.filter(category=cat).count()
                    print(f"  • {cat.name}: {dish_count} 道菜")
            
            elif choice == '9':
                manager.fix_zero_prices()
            
            elif choice == '10':
                manager.fix_all_prices_from_csv()
            
            elif choice == '11':
                manager.reload_and_fix_all()
            
            elif choice == '12':
                print("感謝使用，再見！")
                break
            
            else:
                print("無效的選擇，請輸入 1-12")
        
        except KeyboardInterrupt:
            print("\n\n程式被中斷")
            break
        except Exception as e:
            print(f"發生錯誤: {e}")

if __name__ == "__main__":
    main()