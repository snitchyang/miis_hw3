#!/usr/bin/env python
# coding: utf-8

# In[89]:


import cv2
import re
import numpy as np
import os
import openpyxl
from PIL import Image
from pyzbar import pyzbar
from cnocr import CnOcr

# 发票类
class Invoice:
    def __init__(self,payer='',money='',date=''):
        self.payer=payer
        self.money=money
        self.date=date
    # 交易主体、金额、日期
    payer: str
    money:str
    date:str

# 检查是否符合日期格式
def isDate(string):
    date_pattern = r"\d{4}年\d{2}月\d{2}日"
    if re.match(date_pattern, string):
        return True
    else:
        return False
    
# ocr识别接口，参数为图片地址，返回一个Invoice对象        
def ocr_getinfo(image_path):
    # image_path = datab_path + '\\b'+ str(index)+ '.jpg'
    # 旋转图片使得竖图变横图
    image = Image.open(image_path)
    width, height = image.size
    if width < height:
        image_trans = image.transpose(method=Image.ROTATE_90)
        # 如果旋转了，则保存旋转后的图片
        image_trans.save(image_path)
    # 启动cnocr
    ocr = CnOcr()
    out = ocr.ocr(image_path)
    payer = '深圳市购机汇网络有限公司'
    
    invoice = Invoice()
    
    for i,item in enumerate(out):
        text = item['text']
        # 读取付款人
        # 如果当前内容和'深圳市购机汇网络有限公司'至少有八个字符相同，则可认定他们相同
        if len(set(text) & set(payer))>=8:
            invoice.payer = payer
        # 读取日期
        # 如果当前内容是是开票日期，则下一个大概率是日期
        if '开票日期'in text:
            if isDate(out[i+1]['text']):
                invoice.date = out[i+1]['text']
        # 如果当前内容包含2016年，则这个是日期
        if '2016年'in text:
            substring = '2016年'
            index = text.find(substring)
            if index != -1:
                substring_after = text[index + len(substring):]
            invoice.date = substring + substring_after
        # 如果当前内容符合日期格式，则这个是日期
        if isDate(text):
            invoice.date = text
        # 读取金额
        # 如果当前内容包含小写
        if '小写' in text:
            # 如果当前内容包含 . 则说明小写和金额在同一个内容里
            if '.'in text:
                substring = '小写'
                index = text.find(substring)
                if index != -1:
                    substring_after = text[index+4:]
                invoice.money = substring_after
            # 如果当前内容不含 . 则在当前内容的后四个内容里找含 . 的内容
            else:
                for j in range(4):
                    tmp = str(out[i+j]['text'])
                    if '.' in tmp:
                        if tmp[0].isdigit():
                            invoice.money = tmp
                        else:
                            invoice.money = tmp[1:]
        # 对日期的可能错误进行处理
        string = invoice.date
        if(string!=''):
            # 删除空格字符
            string = string.replace(" ", "")
            # 替换特殊字符
            special_chars = {"s":"8","g":"8","E": "日", "e": "8", "l": "1", "I": "1", "i": "1", "o": "0", "O": "0"}
            for char, replacement in special_chars.items():
                string = string.replace(char, replacement)
            invoice.date = string
            
    return invoice


# In[68]:


# 二维码识别结果的返回格式
class Qrcode_return:
    # 是否识别出二维码、发票代码、发票编号、税前金额、日期
    qrcode_exist: bool
    invoice_code: str
    invoice_num:str
    invoice_amount:str
    invoice_date:str
    def __init__(self,qrcode_exist,invoice_code="",invoice_num="",invoice_amount="",invoice_date=""):
        self.qrcode_exist = qrcode_exist
        self.invoice_code = invoice_code
        self.invoice_num = invoice_num
        self.invoice_amount = invoice_amount
        self.invoice_date = invoice_date
        
# 二维码识别接口，参数为图片地址，返回一个Qrcode_return类     
def qrcode_getinfo(image_path):
    image = Image.open(image_path)
    # 竖图旋转成横图
    width, height = image.size
    if width < height:
        image = image.transpose(method=Image.ROTATE_90)
    # 裁剪出二维码部分
    width, height = image.size
    left = 0
    top = height // 10
    right = width // 4
    bottom = height * 2/5
    cropped_image = image.crop((left, top, right, bottom))
    # 将 PIL 图像转换为 OpenCV 图像数组
    image_array = np.array(cropped_image)
    # 将图像数组转换为灰度图像
    gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    # 使用 Otsu's 二值化方法
    _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 使用pyzbar解码二维码
    qrcodes = pyzbar.decode(binary_image,symbols=[pyzbar.ZBarSymbol.QRCODE])
    if len(qrcodes)==0:
        qrcode_return = Qrcode_return(False)
        return qrcode_return;
    else:
        for qrcode in qrcodes:
            string = qrcode.data.decode('utf-8')
        info = string.split(',')
        qrcode_return = Qrcode_return(True,info[2],info[3],info[4],info[5])
        return qrcode_return;


# In[78]:


# 检验该发票金额是否为浮点数，包含对可能错误的处理
# 是浮点数则返回True，不是则返回False
def is_float(invoice):
    string = invoice.money
    # 检查是否符合浮点数的结构，如果可以转换为浮点数，直接返回 True
    try:
        float(string)
        return True
    except ValueError:
        pass
    # 删除空格字符
    string = string.replace(" ", "")
    # 替换特殊字符
    special_chars = {"日": "8", "s":"8","E": "8", "e": "8","g":"8", "l": "1", "I": "1", "i": "1", "o": "0", "O": "0", "口": "0"}
    for char, replacement in special_chars.items():
        string = string.replace(char, replacement)
    invoice.money = string
    # 再试试能不能转换成浮点数
    try:
        float(string)
        print(string)
        return True
    except ValueError:
        return False


# In[70]:


# 校验二维码中的信息与ocr结果,调整识别结果
# 返回True说明无误，返回False说明存在矛盾，需要人工识别
def check_Ocr_Qrcode(invoice,qrcode):
    # 如果二维码中没有信息，返回真
    if(info2.invoice_amount==''):
        return True
    # 时间信息以二维码结果为准
    date = qrcode.invoice_date
    formatted_date = date[:4] + "年" + date[4:6] + "月" + date[6:8] + "日"
    invoice.date = formatted_date
    # 金额信息确保二维码的税前金额小于实际金额
    if(qrcode.invoice_amount > invoice.money):
        return False
    else: 
        return True


# In[72]:


# 判断时间是否在2016年6月12日之前
def check_time(string):
    # 解析年、月、日
    year = int(string[:4])
    month = int(string[5:7])
    day = int(string[8:10])
    # 比较日期
    if (year < 2016 or (year == 2016 and (month < 6 or (month == 6 and day < 12)))):
        return True
    else:
        return False
    
    
# 检查是否通过
def check(invoice):
    # 检查金额是否小于2700
    if float(invoice.money) > 2700:
        return False
    # 检查付款方是不是"深圳市购机汇网络有限公司"
    if invoice.payer!="深圳市购机汇网络有限公司":
        return False
    return check_time(invoice.date)


# In[94]:


# 流程：使用ocr和qrcode识别所有b数据集的图片
def datab_get_info(datab_folder):
    #需要进行人工检测的下标数组
    manual_work_index =[]
    for filename in os.listdir(datab_folder):
        if filename.endswith(".jpg")or filename.endswith(".png"):
            # 获取图片地址image_path
            image_path = os.path.join(datab_folder, filename)
            # 获取图片下标index
            file_name_without_extension = os.path.splitext(filename)[0]
            number_part = file_name_without_extension[1:]
            index = int(number_part)
            print(index, end=' ')
            
            # 使用ocr识别图片
            invoice = ocr_getinfo(image_path)
            # 如果invoice结果为空，则将图片翻转180度然后重新识别        
            if(invoice.payer==''and invoice.money=='' and invoice.date==''):
                # 旋转图片
                image = Image.open(image_path)
                image_trans = image.transpose(method=Image.ROTATE_180)
                # 保存旋转后的图片
                image_trans.save(image_path)
            invoice = ocr_getinfo(image_path)
            print(invoice.payer, invoice.date, invoice.money)
            # 检查结果是否需要转人工
            # 1.缺少任意一项
            if(invoice.money==''or invoice.payer==''or invoice.date==''):
                manual_work_index.append(index)
                print("转人工")
                continue
            # 2.金额不是浮点数
            if(not is_float(invoice)):
                manual_work_index.append(index)
                print("转人工")
                continue
            
            # 使用qrcode识别图片
            qrcode = qrcode_getinfo(image_path)
            # 如果识别成功
            if(qrcode.invoice_date!=''):
                # 校验二维码中的信息与ocr结果
                check_Ocr_Qrcode(invoice,qrcode)
                
            # 检查是否通过
            if check(invoice):
                print("通过")
            else:
                print("不通过")
    print("转人工的个数为：",len(manual_work_index))    


# In[95]:


datab_folder = 'C:\\Users\\Max\\Desktop\\发票-大数据集\\发票-大数据集\\b'
datab_get_info(datab_folder)

