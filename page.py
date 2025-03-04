import jieba
from ui import AppState, DataMerger, UIHelper, FileHandler
from tqdm import tqdm, trange
from spider import get_search_results, get_custom_info, get_search_result
import asyncio
import pandas as pd
from googletrans import Translator
import time
import sys

import os

class MainApplication:
    def __init__(self):
        self.state = AppState()
        self.search_manager = SearchManager(self.state)
        self.concatenator = DataConcatenator(self.state)
        self.web_search = WebSearchManager(self.state)
        self.hebin = hebin(self.state)

    def show_main_menu(self):
        UIHelper.clear_screen()
        print("""
[1] 爬取数据
[2] 连接数据
[3] 搜索官方网站
[4] 数据处理
[5] 退出
        """)
        choice = UIHelper.get_valid_input("Enter your choice: ", int, {1, 2, 3, 4,5})
        
        if choice == 1:
            self.start_crawling()
        elif choice == 2:
            self.concatenator.start_concatenation()
        elif choice == 3:
            self.web_search.handle_search()
        elif choice == 4:
            a = self.hebin
            a.main()
        elif choice == 5:
            exit()

    def start_crawling(self):
        UIHelper.clear_screen()

        print("""
[E] 返回主菜单
""")
        keyword = input("输入搜索词语: ")
        if keyword.upper() == 'E':
            return self.show_main_menu()
        self.search_manager.handle_search(keyword)

class SearchManager:
    def __init__(self, state: AppState):
        self.state = state

    def handle_search(self, keyword):
        try:
            results = get_search_results(keyword, page=self.state.current_page)
        except:
            print("Failed to get search results, please try again.")
            time.sleep(2)
            return self._return_to_search()
        while True:
            self._display_results(results)
            choice = input(f"Current Page: {self.state.current_page}\nEnter your choice: ").upper()
            
            handlers = {
                'E': lambda: self._return_to_search(),
                'C': lambda: self._show_selection(results, keyword),
                'R': lambda: self._export_selected(),
                'P': lambda: self._change_page(-1, keyword),
                'N': lambda: self._change_page(1, keyword),
            }
            
            if choice.isdigit():
                self._handle_numeric_choice(int(choice), results)
            elif choice in handlers:
                handlers[choice]()
            else:
                print("Invalid choice")

    def _export_selected(self):
        UIHelper.clear_screen()
        for name, url in self.state.selected_companies.items():
            print(f"Getting custom info for {name}")
            info = get_custom_info("https://www.importyeti.com/" + url)
            info.to_excel(f"./data/{name}.xlsx", index=False)
        self.state.reset()
        return self._return_to_main()

    def _change_page(self, direction, keyword):
        self.state.current_page += direction
        if self.state.current_page < 1:
            self.state.current_page = 1
        return self.handle_search(keyword)

    def _handle_numeric_choice(self, choice, results):
        if choice < 1 or choice > len(results):
            return self._display_results(results)
        if choice in self.state.selected_companies:
            return self._display_results(results)
        
        self.state.selected_companies[f'{results[choice-1]["name"]}-{results[choice-1]["country"]}'] = results[choice-1]['url']
        return self._display_results(results)

    def _display_results(self, results):
        UIHelper.clear_screen()
        print("==============Search Results======================")
        for i, result in enumerate(results):
            text = """
    [{index}]\t{name} - {country} - {type}
    \t最新交易时间：{time}   总交易量：{shipment}
    """
            text = text.format(index=i+1, name=result["name"], country=result["country"], type=result["type"], time=result["time"], shipment=result["total"])
            print(text)
        
        print("==============Commands======================")
        print("[E] 返回查询")
        print("[C] 显示当前选择")
        print("[P] 上一页")
        print("[N] 下一页")
        print("[D] 删除数据")
        print("[R] 获取所有选定数据的自定义信息")

        print("==============Selected Options======================")
        for i,v in enumerate(list(self.state.selected_companies.keys())):
            print(f"[{i+1}] {v}")
        return

    def _return_to_main(self):
        app = MainApplication()
        return app.show_main_menu()
    
    def _return_to_search(self):
        app = MainApplication()
        return app.start_crawling()
    
    def _show_selection(self, results, keyword):
        UIHelper.clear_screen()
        companies = list(self.state.selected_companies.keys())
        for i,v in enumerate(companies):
            print(f"[{i+1}] {v}")
        print("[0] Exit")
        try:
            choice = int(input("Input which selected company you want to remove: "))
        except:
            return self._show_selection(results, keyword)
        if choice == 0:
            return self._display_results(results)
        if choice > len(companies):
            return self._show_selection(results, keyword)
        del self.state.selected_companies[companies[choice-1]]
        return self._show_selection(results, keyword)
        

class DataConcatenator:
    def __init__(self, state: AppState):
        self.state = state
        self.DATA_DIR = "./data"

    def start_concatenation(self):
        while True:
            self._display_interface()
            choice = input("Enter your choice: ").upper()
            
            handlers = {
                'A': self._select_all,
                'C': self._show_current_selection,
                'R': self._execute_merge,
                'E': self._return_to_main
            }
            
            if choice.isdigit():
                self._handle_numeric_choice(int(choice))
            elif choice in handlers:
                handlers[choice]()
            else:
                print("Invalid choice")

    def _handle_numeric_choice(self, choice):
        if choice in self.state.selected_files:
            return self._display_interface()
        
        self.state.selected_files[choice] = self.options[choice]
        return self._display_interface()

    def _return_to_main(self):
        app = MainApplication()
        return app.show_main_menu()
    
    def _execute_merge(self):
        full_paths = FileHandler.get_full_paths(self.DATA_DIR, self.state.selected_files.values())
        DataMerger.merge_excel_files(full_paths)
        self.state.reset()
        return self._return_to_main()

    def _display_interface(self):
        UIHelper.clear_screen()
        self.options = {}
        files = FileHandler.get_files("./data")
        for i,v in enumerate(files):
            self.options[i+1] = v

        print("==============Available Options======================")
        for i,v in self.options.items():
            print(f"[{i}] {v}")
        print("")
        print("==============Commands======================")
        print("[A] 选择全部")
        print("[C] 显示当前选择")
        print("[R] 执行连接")
        print("[E] 返回主菜单")

        print("")
        print("==============Selected Options======================")
        print("")

        for i, v in self.state.selected_files.items():
            print(f"[{i}] {v}")
    
    def _select_all(self):
        self.state.selected_files = {i: v for i, v in enumerate(FileHandler.get_files("./data"))}
        return self._display_interface()
    
    def _show_current_selection(self):
        UIHelper.clear_screen()
        for i,v in self.state.selected_files.items():
            print(f"[{i}] {v}")

        print("[0] Exit")
        try:
            choice = UIHelper.get_valid_input("Input which selected file you want to remove: ", int, {0, *range(1, len(self.state.selected_files)+1)})
        except ValueError:
            return self._show_current_selection()
        
        if choice == 0:
            return self._display_interface()

        if choice not in self.state.selected_files:
            return self._show_current_selection()

        del self.state.selected_files[choice]
        return self._show_current_selection()
    
class hebin:
    def __init__(self, state: AppState):
        self.state = state
        #  英文关键词放置
        self.books_keywords = [
            "paper", "gift", "books", "Printde Books", "Children Book", "Printed Cards"
        ]
        # 定义中文相关的关键词
        self.chinese_books_keywords = ["书", "书籍", "儿童书", "绘本", "儿童读物", "学生用品", "笔记本"]

    # 去除重复元素
    def remove_duplicates(self,lst):
        seen = set()
        return [x for x in lst if not (x in seen or seen.add(x))]

    def chinese_process_data(self):
        try:
            print("\n=== 分词处理并提取与书籍相关的关键词 ===")
            # 读取合并结果文件
            file_path = '翻译结果.xlsx'  # 输入文件路径
            df = pd.read_excel(file_path)

            # 检查“中文产品明细”列是否存在
            if '中文产品明细' not in df.columns:
                print("(处理失败) 错误：输入文件中没有找到‘中文产品明细’列。")
                return

            # 定义提取与书籍相关单词的函数
            def extract_books(text):
                if pd.notna(text):  # 如果单元格不为空
                    words = jieba.lcut(text)  # 使用 jieba 进行分词
                    # 提取与书籍相关的关键词（根据匹配库）
                    related_words = [word for word in words if word in self.chinese_books_keywords]
                    # 去除重复的单词
                    unique_words = self.remove_duplicates(related_words)
                    return ' '.join(unique_words)  # 返回提取的关键词
                else:
                    return ""  # 空值保持为空

            # 对“中文产品明细”列进行分词处理并提取相关关键词
            df['关键词'] = df['中文产品明细'].apply(extract_books)

            # 保存到新的 Excel 文件
            output_path = '中文分词结果.xlsx'  # 输出文件路径
            df.to_excel(output_path, index=False)
            print(f"处理完成，结果已保存到 {output_path}！")
        except Exception as e:
            print(f"\n处理失败：{e}")

    # 分词处理并提取与 books 相关的单词
    def process_data(self):
        try:
            print("\n=== 分词处理并提取与 books 相关的单词 ===")
            # 读取合并结果文件
            file_path = '处理文件.xlsx'  # 输入文件路径
            df = pd.read_excel(file_path)

            # 检查“HS Code商品描述”列是否存在
            if 'HS Code商品描述' not in df.columns:
                print("(处理失败) 错误：输入文件中没有找到‘HS Code商品描述’列。")
                return

            # 定义提取与 books 相关单词的函数
            def extract_books(text):
                if pd.notna(text):  # 如果单元格不为空
                    words = jieba.lcut(text)  # 使用 jieba 进行分词
                    # 提取与 books 相关的单词（根据匹配库）
                    related_words = [word for word in words if word.lower() in self.books_keywords]
                    # 去除重复的单词
                    unique_words = self.remove_duplicates(related_words)
                    return ' '.join(unique_words)  # 返回提取的单词
                else:
                    return ""  # 空值保持为空

            # 对“HS Code商品描述”列进行分词处理并提取相关单词
            df['关键词'] = df['HS Code商品描述'].apply(extract_books)

            # 保存到新的 Excel 文件
            output_path = '英文分词结果.xlsx'  # 输出文件路径
            df.to_excel(output_path, index=False)
            print(f"处理完成，结果已保存到 {output_path}！")
        except Exception as e:
            print(f"\n处理失败：{e}")

    async def translatefenci_data(self):
        try:
            print("\n=== 翻译数据 ===")

            # 异步翻译函数
            async def translate_text(text, src_lang, dest_lang):
                translator = Translator()
                translation = await translator.translate(text, src=src_lang, dest=dest_lang)
                return translation.text

            # 主函数
            async def main_translate():
                # 读取Excel文件
                file_path = '英文分词结果.xlsx'  # 输入文件路径
                df = pd.read_excel(file_path)

                # 检查“产品明细”列是否存在
                if '关键词' not in df.columns:
                    print("(翻译失败) 错误：输入文件中没有找到‘关键词’列。")
                    return

                # 提取“产品明细”列的英文数据
                english_product_details = df['关键词'].tolist()

                # 翻译每一项产品明细
                translated_details = []
                for detail in english_product_details:
                    try:
                        if pd.notna(detail):  # 如果单元格不为空
                            translated = await translate_text(detail, 'en', 'zh-cn')
                            translated_details.append(translated)
                        else:
                            translated_details.append("")  # 空值保持为空
                    except Exception as e:
                        translated_details.append(f"翻译失败: {e}")

                # 将翻译结果添加到数据框
                df['中文产品明细'] = translated_details

                # 保存到新的Excel文件
                output_path = '分词翻译结果.xlsx'  # 输出文件路径
                df.to_excel(output_path, index=False)
                print(f"翻译完成，结果已保存到 {output_path}！")

            # 运行异步主函数
            await main_translate()
        except Exception as e:
            print(f"\n翻译失败：{e}")

    def merge_data(self):
        try:
            print("\n=== 数据合并 ===")
            # 读取文件1和文件2
            file1 = pd.read_excel('数据官网.xlsx')  # 文件1包含官网和简介
            file2 = pd.read_excel('处理文件.xlsx')  # 文件3为你从海关获取的数据需要填充官网和简介

            # 合并文件1和文件2，基于“供应商公司名称”列，保留文件2的所有数据
            merged_file = pd.merge(file2, file1[['客户名称', '公司官网', '公司简介']],
                                   on='客户名称', how='left')

            # 将合并后的结果保存为新的Excel文件
            merged_file.to_excel('合并结果.xlsx', index=False)
            print("数据合并完成，结果已保存到 '合并结果.xlsx'！")
        except Exception as e:
            print(f"\n数据合并失败：{e}")

    # 翻译数据功能
    async def translate_data(self):
        try:
            print("\n=== 翻译数据 ===")

            # 异步翻译函数
            async def translate_text(text, src_lang, dest_lang):
                translator = Translator()
                translation = await translator.translate(text, src=src_lang, dest=dest_lang)
                return translation.text

            # 主函数
            async def main_translate():
                # 读取Excel文件
                file_path = '合并结果.xlsx'  # 输入文件路径
                df = pd.read_excel(file_path)

                # 检查“产品明细”列是否存在
                if 'HS Code商品描述' not in df.columns:
                    print("(翻译失败) 错误：输入文件中没有找到‘HS Code商品描述’列。")
                    return

                # 提取“产品明细”列的英文数据
                english_product_details = df['HS Code商品描述'].tolist()

                # 翻译每一项产品明细
                translated_details = []
                for detail in english_product_details:
                    try:
                        if pd.notna(detail):  # 如果单元格不为空
                            translated = await translate_text(detail, 'en', 'zh-cn')
                            translated_details.append(translated)
                        else:
                            translated_details.append("")  # 空值保持为空
                    except Exception as e:
                        translated_details.append(f"翻译失败: {e}")

                # 将翻译结果添加到数据框
                df['中文产品明细'] = translated_details

                # 保存到新的Excel文件
                output_path = '翻译结果.xlsx'  # 输出文件路径
                df.to_excel(output_path, index=False)
                print(f"翻译完成，结果已保存到 {output_path}！")

            # 运行异步主函数
            await main_translate()
        except Exception as e:
            print(f"\n翻译失败：{e}")

    # 主程序
    def main(self):
        while True:
            print("请选择要执行的功能:")
            print("1. 数据合并")
            print("2. 翻译数据")
            print("3. 英文分词处理")
            print("4. 英文分词翻译")
            print("5. 中文分词处理")
            print("6. 退出程序")
            choice = input("\n输入选项（1、2、3、4 ,5或 6！）：")
            if choice == '1':
                self.merge_data()
            elif choice == '2':
                asyncio.run(self.translate_data())
            elif choice == '3':
                self.process_data()
            elif choice == '4':
                asyncio.run(self.translatefenci_data())
            elif choice == '5':
                self.chinese_process_data()
            elif choice == '6':
                print("\n程序已退出。")
                sys.exit()  # 退出程序
            else:
                print("无效的选项，请输入 1、2、3、4 或 5！")

class WebSearchManager:
    def __init__(self, state):
        self.state = state
    
    def handle_search(self):
        UIHelper.clear_screen()
        files = FileHandler.get_files("./output")
        self.options = {i+1: v for i,v in enumerate(files)}
        for i,v in enumerate(files):
            print(f"[{i+1}] {v}")
        
        print("[0] Exit")

        choice = UIHelper.get_valid_input("Enter your choice: ", int, {0, *range(1, len(files)+1)})

        if choice == 0:
            return self._return_to_main()
        
        if choice not in self.options:
            return self.handle_search()

        return self._searching(self.options[choice])
    
    def _searching(self, file):
        UIHelper.clear_screen()
        print(f"Searching for {file}...")
        paths = FileHandler.get_full_paths("./output", [file])
        data = pd.read_excel(paths[0])

        names = list(data[pd.isna(data["公司官网"])]["客户名称"].values)

        for i in tqdm(range(len(names))):
            name = names[i]
            web = get_search_result(name)
            if pd.isna(data.loc[data["客户名称"] == name, "公司官网"]).any() and web:
                data.loc[data["客户名称"] == name, "公司官网"] = web
        data.to_excel(paths[0], index=False)
        return self._return_to_main()
    
    def _return_to_main(self):
        app = MainApplication()
        return app.show_main_menu()