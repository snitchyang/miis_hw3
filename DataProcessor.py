from pymongo import MongoClient
#将每张发票处理结果写入数据库并统计各状态比例以及前k个交易体


# usage：先实例化eg： data_processor = DataProcessor("ocr_result", "ocr")
#每次处理后保存状态 eg： status = "通过" data_processor.save_to_mongodb(index, invoice, status)
#处理完后输出信息以及交易总额前k个交易体eg： top_k = 1  print("前",top_k,"个交易量的交易体为",data_processor.get_top_trading_partners(top_k))  
#例如 在ocr中使用
#  def datab_get_info(datab_folder):
#     data_processor = DataProcessor("ocr_result", "ocr")
#     #需要进行人工检测的下标数组
#     manual_work_index =[]
#     for filename in os.listdir(datab_folder):
#             print(invoice.payer, invoice.date, invoice.money)
#             # 检查结果是否需要转人工
#             # 1.缺少任意一项
#             if(invoice.money==''or invoice.payer==''or invoice.date==''):
#                 manual_work_index.append(index)
#                 status = "转人工"
#                 data_processor.save_to_mongodb(index, invoice, status)
#                 print("转人工")
#                 continue
#             # 2.金额不是浮点数
#             if(not is_float(invoice)):
#                 manual_work_index.append(index)
#                 status = "转人工"
#                 data_processor.save_to_mongodb(index, invoice, status)
#                 print("转人工")
#                 continue
#             # 检查是否通过
#             if check(invoice):
#                 status = "通过"
#                 data_processor.save_to_mongodb(index, invoice, status)
#                 print("通过")
#             else:
#                 status = "不通过"
#                 data_processor.save_to_mongodb(index, invoice, status)
#                 print("不通过")
#     data_processor.print_info() 输出信息
#     top_k = 1  
#     print("前",top_k,"个交易量的交易体为",data_processor.get_top_trading_partners(top_k))  
class DataProcessor:
    def __init__(self, db_name, collection_name):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.total_invoices = 0
        self.approved = 0
        self.rejected = 0
        self.manual_work = 0
        self.trading_partners = {}  # 记录交易方和交易总额的字典

    def save_to_mongodb(self, index, invoice, status):
        money_value = None
        if invoice.money and invoice.money.strip():
            try:
                money_value = float(invoice.money)
            except ValueError:
                pass

        self.total_invoices += 1
        if status == "通过":
            self.approved += 1
            if invoice.payer in self.trading_partners:
                self.trading_partners[invoice.payer] += money_value
            else:
                self.trading_partners[invoice.payer] = money_value
        elif status == "不通过":
            self.rejected += 1
            if invoice.payer in self.trading_partners:
                self.trading_partners[invoice.payer] += money_value
            else:
                self.trading_partners[invoice.payer] = money_value
        elif status == "转人工":
            self.manual_work += 1

        data = {
            "index": index,
            "status": status,
            "details": f"{index} {invoice.payer} {invoice.date} {money_value}"
        }
        self.collection.insert_one(data)

    def get_pass_number(self):
        return self.approved
    
    def get_rejected_number(self):
        return self.rejected
    
    def get_manual_number(self):
        return self.manual_work
    
    def print_info(self):
        print("转人工的个数为：", self.manual_work)  
        print("通过的个数为：", self.approved)  
        print("拒绝的个数为：", self.rejected)  

    def get_top_trading_partners(self, k):
        sorted_partners = sorted(self.trading_partners.items(), key=lambda x: x[1], reverse=True)
        return sorted_partners[:k]


