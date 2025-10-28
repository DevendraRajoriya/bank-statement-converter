class ExcelGenerator:
    def __init__(self, data):
        self.data = data

    def generate_excel(self, file_name):
        import pandas as pd
        df = pd.DataFrame(self.data)
        df.to_excel(file_name, index=False)

    def add_sheet(self, sheet_name, data):
        import pandas as pd
        df = pd.DataFrame(data)
        with pd.ExcelWriter(sheet_name + '.xlsx', mode='a') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)