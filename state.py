class State:
    page = 1
    keyword = ""
    customs_result_list = []
    selected_companies = {}
    error_info = ""
    tree_selected_file = ''
    def clean(self):
        self.page = 1
        self.keyword = ""
        self.customs_result_list = []
        self.selected_companies = {}
        self.error_info = ""
        self.tree_selected_file = ''
state = State()