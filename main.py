import os
import re
import time
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, OptionList ,Label, Button, Input, Checkbox, ProgressBar, DirectoryTree
from textual.containers import VerticalScroll, HorizontalScroll, Center, Middle, Container
from textual import events, on
from textual.widgets.option_list import Option
from textual.screen import Screen
from spider import get_search_results_async, get_custom_info_async, get_company_intro_async, translate_goods_async, searach_for_official_website
from state import state
from textual.reactive import reactive
from textual.widget import Widget
import pandas as pd
from textual import work
from config import config

class DataMerger:
    @staticmethod
    def merge_excel_files(paths):
        dfs = [pd.read_excel(p) for p in paths]
        combined = pd.concat(dfs, ignore_index=True)
        combined.sort_values(by="海关提单时间", ascending=False, inplace=True)
        combined.drop_duplicates(subset=["客户名称"], keep="first", inplace=True)
        return combined

class FileHandler:
    @staticmethod
    def get_files(directory):
        return next(os.walk(directory))[2]

    @staticmethod
    def get_full_paths(directory, filenames):
        return [os.path.join(directory, f) for f in filenames]

# 第一个选项
class DetailSearching(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]

    def compose(self):
        yield Header()
        yield Label("[b]正在爬取海关数据详情...[/b]")
        with Center():
            with Middle():
                yield ProgressBar(id="crawling_progress", total=len(state.selected_companies))
        yield Footer()

    async def on_mount(self) -> None:
        self.refresh(recompose=True)
        self.title = "爬取详情"
        self.sub_title = f"正在爬取{len(state.selected_companies)}个海关数据详情"
        self.runing()

    @work(exclusive=True)
    async def runing(self):
        for i, (key, value) in enumerate(state.selected_companies.items()):
            data = await get_custom_info_async("https://www.importyeti.com/" + value)
            if data is not None:
                sanitized_key = re.sub(r"[\/\\\:\*\?\"\<\>\|]", " ", key)
                data.to_excel(f"./data/{sanitized_key}.xlsx", index=False)
            else:
                print(f"爬取失败：{key}")
            self.query_one("#crawling_progress").advance(1)
        
        time.sleep(2)
        state.clean()
        app.pop_screen()
        app.uninstall_screen("detail_searching")

class SearchReult(Screen):
    BINDINGS = [
        ("escape", "", "返回上一页")
    ]

    show_sidebar = reactive(False)

    def compose(self):
        if state.page not in state.selection_for_page:
            state.selection_for_page[state.page] = []
        yield Header()
        with VerticalScroll(id="result"):
            for i, result in enumerate(state.customs_result_list):
                text = "[{index}] {name} - {country} - {type} 最新交易时间：{time} 总交易量：{shipment}"
                yield Checkbox(text.format(index=i+1, name=result["name"], country=result["country"], type=result["type"], time=result["time"], shipment=result["total"]), id=f"r{i+1}")
        with HorizontalScroll():
            yield Button("上一页", id="prev_button", variant="primary", disabled=state.page == 1)
            yield Button("下一页", id="next_button", variant="primary")
            yield Button("爬取详情", id="detail_button", variant="primary", disabled=len(state.selected_companies) == 0)
        yield Footer()
    
    def on_mount(self) -> None:
        self.title = "搜索结果"
        self.sub_title = f"第{state.page}页"

        current_page_selection = state.selection_for_page[state.page]
        if len(current_page_selection) == 0:
            return
        for id in current_page_selection:
            checkbox = self.query_one(f"#{id}")
            checkbox.value = True
    
    @on(Checkbox.Changed)
    def save_selection(self, event: Checkbox.Changed) -> None:
        index = int(event.checkbox.id[1:])
        if event.value:
            state.selection_for_page[state.page].append(event.checkbox.id)
            state.selected_companies[f'{state.customs_result_list[index-1]["name"]}-{state.customs_result_list[index-1]["country"]}'] = state.customs_result_list[index-1]['url']
        else:
            del state.selected_companies[f'{state.customs_result_list[index-1]["name"]}-{state.customs_result_list[index-1]["country"]}']
            state.selection_for_page[state.page].remove(event.checkbox.id)
        
        if len(state.selected_companies) > 0:
            self.query_one("#detail_button").disabled = False
        else:
            self.query_one("#detail_button").disabled = True
    
    @on(Button.Pressed, "#detail_button")
    def detail_button_pressed(self, event: Button.Pressed):
        app.pop_screen()
        app.push_screen(DetailSearching())
    
    @on(Button.Pressed, "#prev_button")
    async def prev_button_pressed(self, event: Button.Pressed):
        await self.change_page(-1)
    
    @on(Button.Pressed, "#next_button")
    async def next_button_pressed(self, event: Button.Pressed):
        await self.change_page(1)
    
    async def change_page(self, direction: int):
        state.page = max(1, state.page + direction)
        state.customs_result_list = await get_search_results_async(state.keyword, state.page)
        app.switch_screen(SearchReult())

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            state.clean()
            app.switch_screen(SearchingScreen())

class SearchingScreen(Screen):
    SEARCHING_COMMANDS = """
[b]importyeti的搜索命令[/b]

""        精确搜索

| (OR)    返回包含任意一个词的结果

& (AND)   返回所有包含所有词的结果

-         排除包含该词的结果

*         通配符

()        分组搜索
"""
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]

    def compose(self):
        yield Header()
        yield Label(self.SEARCHING_COMMANDS)
        with HorizontalScroll():
            yield Input(id="search_input", placeholder="输入搜索关键词")
            yield Button("搜索", id="search_button", variant="primary", disabled=True)
        yield Footer()
    
    def on_mount(self) -> None:
        self.title = "爬取importyeti"

    @on(Input.Changed, "#search_input")
    def search_input_changed(self, event: Input.Changed):
        if event.value:
            self.query_one("#search_button").disabled = False
        else:
            self.query_one("#search_button").disabled = True

    @on(Button.Pressed, "#search_button")
    async def search_button_pressed(self, event: Button.Pressed):
        search_query = self.query_one("#search_input").value
        state.keyword = search_query
        state.customs_result_list = await get_search_results_async(state.keyword, state.page)
        app.push_screen(SearchReult())

# 第二个选项
class ConcateManger(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]


    def compose(self):
        self.SELECTED_FILES = []
        self.OUTPUT_DATA = ""
        self.FILES = FileHandler.get_files("./data")
        yield Header()
        with VerticalScroll(id="concat_option_container", disabled=False):
            for i, v in enumerate(self.FILES):
                yield Checkbox(
                    f"[{i+1}] {v}",
                    id=f"f{i}"
                )
        yield Button("合并", id="concat_button", variant="primary", disabled=True, classes="inline_buttom")
        with Container(id="output_input_container", classes="hidden"):
            yield Input(id="output_input", placeholder="输出文件名")
            with HorizontalScroll():
                yield Button("保存", id="save_button", variant="primary", disabled=True, classes="inline_buttom")
                yield Button("取消", id="cancel_button", variant="warning", classes="inline_buttom")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "合并数据文件"

    @on(Input.Changed, "#output_input")
    def output_input_changed(self, event: Input.Changed):
        if event.value:
            self.query_one("#save_button").disabled = False
        else:
            self.query_one("#save_button").disabled = True
    
    @on(Checkbox.Changed)
    def save_selection(self, event: Checkbox.Changed):
        index = int(event.checkbox.id[1:])
        if event.value:
            self.SELECTED_FILES.append(self.FILES[index])
        else:
            self.SELECTED_FILES.remove(self.FILES[index])
        if len(self.SELECTED_FILES) < 1:
            self.query_one("#concat_button").disabled = True
        else:
            self.query_one("#concat_button").disabled = False
    
    @on(Button.Pressed, "#cancel_button")
    def cancel_button_pressed(self, event: Button.Pressed):
        self.query_one("#output_input_container").add_class("hidden")
        self.query_one("#concat_button").remove_class("hidden")
        self.query_one("#concat_option_container").disabled = False

    @on(Button.Pressed, "#concat_button")
    def concat_button_pressed(self, event: Button.Pressed):
        full_paths = FileHandler.get_full_paths("./data", self.SELECTED_FILES)
        self.OUTPUT_DATA = DataMerger.merge_excel_files(full_paths)
        self.query_one("#concat_button").add_class("hidden")
        self.query_one("#output_input_container").remove_class("hidden")
        self.query_one("#concat_option_container").disabled = True

    @on(Button.Pressed, "#save_button")
    def save_button_pressed(self, event: Button.Pressed):
        output_file_name = self.query_one("#output_input").value
        state.clean()
        self.OUTPUT_DATA.to_excel(f"./output/{output_file_name}.xlsx", index=False)
        app.pop_screen()

# 第三个选项
class WebSearching(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]

    def compose(self):
        self.data = pd.read_excel(state.tree_selected_file)
        self.names = list(self.data[pd.isna(self.data["公司官网"])]["客户名称"].values)
        yield Header()
        with Center():
            with Middle():
                yield ProgressBar(id="searching_progress", total=len(self.names))
        yield Footer()
    
    @work(exclusive=True)
    async def runing(self):
        for i, name in enumerate(self.names):
            web = await searach_for_official_website(name)
            if pd.isna(self.data.loc[self.data["客户名称"] == name, "公司官网"]).any() and web:
                self.data.loc[self.data["客户名称"] == name, "公司官网"] = web
            self.query_one("#searching_progress").advance(1)
        self.data.to_excel(state.tree_selected_file, index=False)
        app.pop_screen()

    async def on_mount(self) -> None:
        self.refresh(recompose=True)
        self.title = "搜索官网"
        self.sub_title = f"正在搜索{len(self.names)}个公司的官网"
        self.runing()

class WebSearchManager(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]

    def compose(self):
        state.clean()
        yield Header()
        yield DirectoryTree("./output", id="ws_directory_tree", classes="tree")
        with Center():
            yield Button("查找", id="search_button", classes="inline_buttom" ,variant="primary", disabled=True)
        yield Footer()
    
    def on_mount(self) -> None:
        self.title = "官网查找"
    
    @on(DirectoryTree.FileSelected, "#ws_directory_tree")
    def file_selected(self, event: DirectoryTree.FileSelected):
        state.tree_selected_file = event.path
        self.query_one("#search_button").disabled = False

    @on(Button.Pressed, "#search_button")
    def search_button_pressed(self, event: Button.Pressed):
        app.push_screen(WebSearching())

# 第四个选项
class Translating(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]

    def compose(self):
        self.data = pd.read_excel(state.tree_selected_file)
        self.contents = self.data["HS Code商品描述"].values
        self.data["中文产品明细"] = None
        yield Header()
        with Center():
            with Middle():
                yield ProgressBar(id="translating_progress", total=len(self.contents))
        yield Footer()
    
    @work(exclusive=True)
    async def runing(self):
        for i, content in enumerate(self.contents):
            if pd.isna(content): 
                continue
            translated_content = await translate_goods_async(content)
            if not translated_content:
                continue

            self.data.loc[self.data["HS Code商品描述"] == content, "中文产品明细"] = translated_content
            self.query_one("#translating_progress").advance(1)

        self.data.to_excel(state.tree_selected_file, index=False)
        app.pop_screen()

    async def on_mount(self) -> None:
        self.refresh(recompose=True)
        self.title = "翻译产品明细"
        self.sub_title = f"正在翻译{len(self.contents)}条结果"
        self.runing()

class TranslatorManager(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]

    def compose(self):
        state.clean()
        yield Header()
        yield DirectoryTree("./output", id="ts_directory_tree", classes="tree")
        with Center():
            yield Button("翻译", id="trans_button", variant="primary", disabled=True, classes="inline_buttom")
        yield Footer()
    
    def on_mount(self) -> None:
        self.title = "产品翻译"
    
    @on(DirectoryTree.FileSelected, "#ts_directory_tree")
    def file_selected(self, event: DirectoryTree.FileSelected):
        state.tree_selected_file = event.path
        self.query_one("#trans_button").disabled = False

    @on(Button.Pressed, "#trans_button")
    def search_button_pressed(self, event: Button.Pressed):
        app.push_screen(Translating())

# 第五个选项
class IntroGenerating(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]

    def compose(self):
        self.data = pd.read_excel(state.tree_selected_file)
        self.names = list(self.data[pd.isna(self.data["公司简介"])]["客户名称"].values)
        yield Header()
        with Center():
            with Middle():
                yield ProgressBar(id="intro_progress", total=len(self.names))
        yield Footer()

    @work(exclusive=True)
    async def runing(self):
        for i, name in enumerate(self.names):
            web = self.data.loc[self.data["客户名称"] == name, "公司官网"].values[0]
            intro = await get_company_intro_async(name, web)
            self.query_one("#intro_progress").advance(1)
            if not intro or "无相关信息" in intro:
                continue
            if pd.isna(self.data.loc[self.data["客户名称"] == name, "公司简介"]).any() and intro:
                self.data.loc[self.data["客户名称"] == name, "公司简介"] = intro
        self.data.to_excel(state.tree_selected_file, index=False)
        app.pop_screen()
    
    def on_mount(self) -> None:
        self.refresh(recompose=True)
        self.title = "简介生成中"
        self.sub_title = f"正在生成{len(self.names)}条简介"
        self.runing()

class IntroGenerator(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]

    def compose(self):
        state.clean()
        yield Header()
        yield DirectoryTree("./output", id="intro_directory_tree", classes="tree")
        with Center():
            yield Button("AI生成简介", id="intro_button", variant="primary", disabled=True, classes="inline_buttom")
        yield Footer()
    
    def on_mount(self) -> None:
        self.title = "简介生成"
    
    @on(DirectoryTree.FileSelected, "#intro_directory_tree")
    def file_selected(self, event: DirectoryTree.FileSelected):
        state.tree_selected_file = event.path
        self.query_one("#intro_button").disabled = False

    @on(Button.Pressed, "#intro_button")
    def search_button_pressed(self, event: Button.Pressed):
        app.push_screen(IntroGenerating())

# 第六个选项
class InputWithLabel(Widget):
    """An input with a label."""

    DEFAULT_CSS = """
    InputWithLabel {
        layout: horizontal;
        height: auto;
    }
    InputWithLabel Label {
        padding: 1;
        width: 12;
        text-align: right;
    }
    InputWithLabel Input {
        width: 1fr;
    }
    """

    BINDINGS = [
        ("ctrl+delete", "clear_all", "清空输入"),
    ]

    def __init__(self, input_label: str, id: str = "", default_value: str = "") -> None:
        self.input_label = input_label
        self.default_value = default_value
        self.ids = id
        super().__init__()

    def compose(self) -> ComposeResult:  
        yield Label(self.input_label)
        yield Input(value=self.default_value, id=self.ids)
    
    def action_clear_all(self) -> None:
        self.query_one(Input).clear()

class Setting(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "返回上一页"),
    ]
    def compose(self):
        yield Header()
        yield InputWithLabel("API Key", id="api_key", default_value=config.api_key)
        yield InputWithLabel("Importyeti Cookie - 列表搜索", id="importyeti_cookie_searching", default_value=config.importyeti_cookie_searching)
        yield InputWithLabel("Importyeti Cookie - 详情搜索", id="importyeti_cookie_details", default_value=config.importyeti_cookie_details)
        yield InputWithLabel("Bing Cookie", id="bing_cookie", default_value=config.bing_cookie)
        yield Button("保存", id="config_save_button", variant="primary", classes="inline_buttom")
        yield Footer()
    
    def on_mount(self):
        self.title = "设置"
        print(config.api_key)

    @on(Button.Pressed, "#config_save_button")
    def on_save_button_pressed(self, event: Button.Pressed):
        config.api_key = self.query_one("#api_key").value
        config.importyeti_cookie_searching = self.query_one("#importyeti_cookie_searching").value
        config.importyeti_cookie_details = self.query_one("#importyeti_cookie_details").value
        config.bing_cookie = self.query_one("#bing_cookie").value
        config.save()

class MainApplication(App):
    CSS_PATH = "style.css"
    BINDINGS = [
        ("ctrl+q", "app.quit", "Quit"),
    ]
    SCREENS={
        "searching": SearchingScreen,
    }

    def compose(self):
        yield Header()
        yield Footer()
        with Center():
            yield OptionList(
                Option("爬取importyeti", id="importyeti"),
                Option("合并数据", id="concat"),
                Option("官网查找", id="offi"),
                Option("产品翻译", id="trans"),
                Option("简介生成", id="intro"),
                Option("设置", id="setting"),
                Option("退出", id="quit"),
                id="main_menu",
            )
    
    def on_mount(self) -> None:
        self.title = "Customs Crawler"

    @on(OptionList.OptionSelected, "#main_menu")
    def option_clicked(self, event: OptionList.OptionSelected) -> None:
        if event.option.id == "importyeti":
            self.push_screen("searching")
        elif event.option.id == "concat":
            self.push_screen(ConcateManger())
        elif event.option.id == "offi":
            self.push_screen(WebSearchManager())
        elif event.option.id == "trans":
            self.push_screen(TranslatorManager())
        elif event.option.id == "intro":
            self.push_screen(IntroGenerator())
        elif event.option.id == "setting":
            self.push_screen(Setting())
        elif event.option.id == "quit":
            app.exit()
        

if __name__ == "__main__":
    app = MainApplication()
    app.run()