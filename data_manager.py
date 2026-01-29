import os
import sys
import pandas as pd
import re
from datetime import datetime

# 添加 Django 設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_project.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from menu.models import Dish, Category, MealTime

class DataManager:
    def __init__(self):
        self.df = None
        
    def load_csv(self, file_path):
        """載入 CSV 檔案"""
        try:
            self.df = pd.read_csv(file_path)
            print(f"成功載入檔案: {file_path}")
            print(f"資料筆數: {len(self.df)}")
            return True
        except Exception as e:
            print(f"載入檔案失敗: {e}")
            return False
    
    def clean_data(self):
        """清理資料"""
        if self.df is None:
            print("請先載入資料")
            return False
        
        print("開始清理資料...")
        
        # 清理每一列
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                self.df[col] = self.df[col].astype(str).apply(self._clean_string)
        
        # 處理供應時段
        self._process_meal_times()
        
        print("資料清理完成")
        return True
    
    def _clean_string(self, text):
        """清理字串"""
        if pd.isna(text):
            return ""
        
        # 移除特殊符號
        text = re.sub(r'[#$%^&*()_+=\[\]{}|;:"<>?/~`]', '', str(text))
        
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
        text = text.strip()
        
        # 處理價格和熱量的清理
        if '價格' in str(text) or '熱量' in str(text):
            # 移除非數字字符，保留小數點
            text = re.sub(r'[^\d.]', '', text)
        
        return text
    
    def _process_meal_times(self):
        """處理供應時段欄位"""
        if '供應時段' in self.df.columns:
            # 確保所有值都是字串
            self.df['供應時段'] = self.df['供應時段'].astype(str)
            
            # 分割多個時段
            def split_meal_times(times):
                if pd.isna(times):
                    return []
                # 使用逗號或空格分割
                return [t.strip() for t in re.split(r'[,\s]+', str(times)) if t.strip()]
            
            self.df['meal_times_list'] = self.df['供應時段'].apply(split_meal_times)
    
    def format_data(self):
        """格式化資料"""
        print("格式化資料...")
        
        # 確保欄位存在
        required_columns = ['菜名', '主要食材', '供應時段', '價格(元)', '熱量(卡路里)']
        for col in required_columns:
            if col not in self.df.columns:
                print(f"錯誤: 缺少必要欄位: {col}")
                return False
        
        # 轉換資料型態
        try:
            self.df['價格(元)'] = pd.to_numeric(self.df['價格(元)'], errors='coerce')
            self.df['熱量(卡路里)'] = pd.to_numeric(self.df['熱量(卡路里)'], errors='coerce').fillna(0).astype(int)
        except Exception as e:
            print(f"轉換數值失敗: {e}")
            return False
        
        print("資料格式化完成")
        return True
    
    def import_to_db(self):
        """匯入資料到資料庫"""
        if self.df is None:
            print("請先載入並清理資料")
            return False
        
        print("開始匯入資料到資料庫...")
        
        imported_count = 0
        error_count = 0
        
        for _, row in self.df.iterrows():
            try:
                # 取得或創建食材類別
                category_name = self._clean_string(row['主要食材'])
                category, _ = Category.objects.get_or_create(name=category_name)
                
                # 取得或創建供應時段
                meal_times = []
                if hasattr(row, 'meal_times_list'):
                    for meal_time_name in row.meal_times_list:
                        meal_time, _ = MealTime.objects.get_or_create(name=meal_time_name)
                        meal_times.append(meal_time)
                
                # 創建或更新菜餚
                dish, created = Dish.objects.update_or_create(
                    name=row['菜名'],
                    defaults={
                        'category': category,
                        'price': float(row['價格(元)']),
                        'calories': int(row['熱量(卡路里)']),
                    }
                )
                
                # 設定供應時段
                if meal_times:
                    dish.meal_times.set(meal_times)
                
                if created:
                    imported_count += 1
                
            except Exception as e:
                print(f"匯入 {row.get('菜名', '未知')} 失敗: {e}")
                error_count += 1
        
        print(f"匯入完成! 成功: {imported_count}, 失敗: {error_count}")
        return True
    
    def export_to_csv(self, file_path):
        """從資料庫匯出到 CSV"""
        try:
            dishes = Dish.objects.all().select_related('category').prefetch_related('meal_times')
            
            data = []
            for dish in dishes:
                meal_times = ','.join([mt.name for mt in dish.meal_times.all()])
                data.append({
                    '菜名': dish.name,
                    '主要食材': dish.category.name,
                    '供應時段': meal_times,
                    '價格(元)': float(dish.price),
                    '熱量(卡路里)': dish.calories
                })
            
            df_export = pd.DataFrame(data)
            df_export.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            print(f"成功匯出到: {file_path}")
            print(f"匯出筆數: {len(df_export)}")
            return True
            
        except Exception as e:
            print(f"匯出失敗: {e}")
            return False
    
    def list_dishes(self, limit=20):
        """列出菜餚"""
        dishes = Dish.objects.all().select_related('category')[:limit]
        
        print(f"\n{'菜名':<20} {'主要食材':<10} {'價格':<8} {'熱量':<8} {'時段':<15}")
        print("-" * 70)
        
        for dish in dishes:
            meal_times = ','.join([mt.name for mt in dish.meal_times.all()])
            print(f"{dish.name[:18]:<20} {dish.category.name[:8]:<10} ¥{dish.price:<7} {dish.calories:<8} {meal_times[:14]:<15}")
        
        print(f"\n總計: {Dish.objects.count()} 筆記錄")
    
    def delete_all_data(self):
        """刪除所有資料"""
        confirm = input("確定要刪除所有資料嗎？(yes/no): ")
        if confirm.lower() == 'yes':
            Dish.objects.all().delete()
            Category.objects.all().delete()
            MealTime.objects.all().delete()
            print("所有資料已刪除")
        else:
            print("取消刪除")

def main():
    """主程式"""
    manager = DataManager()
    
    while True:
        print("\n" + "="*50)
        print("食物菜單資料管理系統")
        print("="*50)
        print("1. 載入 CSV 檔案")
        print("2. 清理資料")
        print("3. 格式化資料")
        print("4. 匯入到資料庫")
        print("5. 從資料庫匯出到 CSV")
        print("6. 列出所有菜餚")
        print("7. 刪除所有資料")
        print("8. 執行完整匯入流程")
        print("9. 離開")
        print("="*50)
        
        choice = input("請選擇操作 (1-9): ")
        
        if choice == '1':
            file_path = input("請輸入 CSV 檔案路徑: ")
            manager.load_csv(file_path)
        
        elif choice == '2':
            manager.clean_data()
        
        elif choice == '3':
            manager.format_data()
        
        elif choice == '4':
            manager.import_to_db()
        
        elif choice == '5':
            file_path = input("請輸入匯出檔案路徑: ")
            manager.export_to_csv(file_path)
        
        elif choice == '6':
            manager.list_dishes()
        
        elif choice == '7':
            manager.delete_all_data()
        
        elif choice == '8':
            # 完整流程
            file_path = input("請輸入 CSV 檔案路徑: ")
            if manager.load_csv(file_path):
                manager.clean_data()
                manager.format_data()
                manager.import_to_db()
        
        elif choice == '9':
            print("再見！")
            break
        
        else:
            print("無效的選擇，請重新輸入")

if __name__ == "__main__":
    main()