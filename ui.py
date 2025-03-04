import os
import pandas as pd

class AppState:
    def __init__(self):
        self.selected_files = {}
        self.selected_companies = {}
        self.current_page = 1
    
    def reset(self):
        self.selected_files = {}
        self.selected_companies = {}
        self.current_page = 1

class DataMerger:
    @staticmethod
    def merge_excel_files(paths):
        dfs = [pd.read_excel(p) for p in paths]
        combined = pd.concat(dfs, ignore_index=True)
        combined.sort_values(by="海关提单时间", ascending=False, inplace=True)
        combined.drop_duplicates(subset=["客户名称"], keep="first", inplace=True)
        output_path = os.path.join(os.getcwd(), "处理文件.xlsx")
        combined.to_excel(output_path, index=False)

class FileHandler:
    @staticmethod
    def get_files(directory):
        return next(os.walk(directory))[2]

    @staticmethod
    def get_full_paths(directory, filenames):
        return [os.path.join(directory, f) for f in filenames]

class UIHelper:
    @staticmethod
    def clear_screen():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def get_valid_input(prompt, input_type=int, valid_options=None):
        while True:
            try:
                value = input_type(input(prompt))
                if valid_options and value not in valid_options:
                    raise ValueError
                return value
            except ValueError:
                print("Invalid input, please try again.")