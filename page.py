from ui import AppState, DataMerger, UIHelper, FileHandler
from tqdm import tqdm, trange
from spider import get_search_results, get_custom_info, get_search_result
import asyncio
import pandas as pd
from googletrans import Translator
import time

class MainApplication:
    def __init__(self):
        self.state = AppState()
        self.search_manager = SearchManager(self.state)
        self.concatenator = DataConcatenator(self.state)
        self.web_search = WebSearchManager(self.state)
        self.translator = TranslatorManager(self.state)

    def show_main_menu(self):
        UIHelper.clear_screen()
        print("""
[1] Crawl data
[2] Concatenate data
[3] Search for official website
[4] Translate the goods name
[5] Quit
        """)
        choice = UIHelper.get_valid_input("Enter your choice: ", int, {1, 2, 3, 4})
        
        if choice == 1:
            self.start_crawling()
        elif choice == 2:
            self.concatenator.start_concatenation()
        elif choice == 3:
            self.web_search.handle_search()
        elif choice == 4:
            self.translator.handle_translate()
        elif choice == 5:
            exit()

    def start_crawling(self):
        UIHelper.clear_screen()
        print("""
$$$$$$\                                               $$\     $$\     $$\             $$\     $$\ 
\_$$  _|                                              $$ |    \$$\   $$  |            $$ |    \__|
  $$ |  $$$$$$\$$$$\   $$$$$$\   $$$$$$\   $$$$$$\  $$$$$$\    \$$\ $$  /  $$$$$$\  $$$$$$\   $$\ 
  $$ |  $$  _$$  _$$\ $$  __$$\ $$  __$$\ $$  __$$\ \_$$  _|    \$$$$  /  $$  __$$\ \_$$  _|  $$ |
  $$ |  $$ / $$ / $$ |$$ /  $$ |$$ /  $$ |$$ |  \__|  $$ |       \$$  /   $$$$$$$$ |  $$ |    $$ |
  $$ |  $$ | $$ | $$ |$$ |  $$ |$$ |  $$ |$$ |        $$ |$$\     $$ |    $$   ____|  $$ |$$\ $$ |
$$$$$$\ $$ | $$ | $$ |$$$$$$$  |\$$$$$$  |$$ |        \$$$$  |    $$ |    \$$$$$$$\   \$$$$  |$$ |
\______|\__| \__| \__|$$  ____/  \______/ \__|         \____/     \__|     \_______|   \____/ \__|
                      $$ |                                                                        
                      $$ |                                                                        
                      \__|                                                                        
""")
        print("""
Operator\tFunction
          
""\tReturns results with the exact term or phrase
          
| (OR)\tReturns results with either of the terms used
          
+ (AND)\tReturns results with both terms used
          
-\tReturns results without the term used
          
*\tActs as a placeholder for any term or phrase, like fill in the blanks.

()\tGroups multiple operators for a more refined search.

========================================================================================================
[E] Return to main menu
""")
        keyword = input("Enter the search keyword: ")
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
        print("[E] Return to search")
        print("[C] Show Current Selection")
        print("[P] Previous Page")
        print("[N] Next Page")
        print("[R] Get all selected data's custom info")

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
        print("[A] Select all")
        print("[C] Show Current Selection")
        print("[R] Execute Concatenation")
        print("[E] Return to main menu")

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
    
class TranslatorManager:
    def __init__(self, state: AppState):
        self.state = state
        self.translator = Translator()
    
    def handle_translate(self):
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
            return self.handle_translate()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._translating(self.options[choice]))

    async def _translating(self, file):
        UIHelper.clear_screen()
        try:
            print("\n翻译中...")
             # 异步翻译函数
            async def translate_text(text, src_lang, dest_lang):
                translator = Translator()
                translation = await translator.translate(text, src=src_lang, dest=dest_lang)
                return translation.text
            # 主函数
            async def main_translate():
                file_path = f"./output/{file}"
                df = pd.read_excel(file_path)

                # 检查“产品明细”列是否存在
                if 'HS Code商品描述' not in df.columns:
                    print("(翻译失败) 错误：输入文件中没有找到‘HS Code商品描述’列。")
                    return
                
                # 提取“产品明细”列的英文数据
                english_product_details = df['HS Code商品描述'].tolist()


                # 翻译每一项产品明细
                translated_details = []
                for i in trange(len(english_product_details)):
                    detail = english_product_details[i]
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

                df.to_excel(file_path, index=False)
             # 运行异步主函数
            await main_translate()
            self._return_to_main()
        except Exception as e:
            print(f"\n翻译失败：{e}")
            self._return_to_main()

    def _return_to_main(self):
        app = MainApplication()
        return app.show_main_menu()

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