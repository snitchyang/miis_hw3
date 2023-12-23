import cv2
import re
import numpy as np
from PIL import Image
from pyzbar import pyzbar
from cnocr import CnOcr
import scipy
import os
import pytesseract
from pytesseract import Output
import re

#发票类
class Invoice:
    def __init__(self,payer='',money='',date=''):
        self.payer=payer
        self.money=money
        self.date=date
    # 交易主体、金额、日期
    payer: str
    money:str
    date:str

class ImageStatus:
    def __init__(self, image_path, status=""):
        self.image_path = image_path
        self.status = None
        

#检查是否符合日期格式
def isDate(string):
    date_pattern = r"\d{4}年\d{2}月\d{2}日"
    if re.match(date_pattern, string):
        return True
    else:
        return False
    
import cv2
import numpy as np

def rotate_image_to_normal(image):
    # 将PIL Image转换为OpenCV格式
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # 使用OpenCV进行文本方向检测
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)

    # 计算角度
    if lines is not None:
        angles = [line[0][1] for line in lines]
        angle = np.median(angles) * 180 / np.pi
    else:
        angle = 0.0

    # 根据方向进行旋转
    if angle != 0:
        center = tuple(np.array(opencv_image.shape[1::-1]) / 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, -angle, 1.0)
        opencv_image = cv2.warpAffine(opencv_image, rotation_matrix, opencv_image.shape[1::-1], flags=cv2.INTER_LINEAR)
    
    # 将OpenCV格式转换回PIL Image
    rotated_image = Image.fromarray(cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB))
    
    return rotated_image



# 获取图像的分辨率信息
def get_image_resolution(image_path):
    image = Image.open(image_path)
    dpi = image.info.get('dpi', (0, 0))
    return dpi


def ocr_getinfo(index):
    # 检查image_path是否存在
    image_path = 'C://Users//Martin//Desktop//FP_dataset//a//a'+str(index)+'.jpg'
    if not os.path.exists(image_path):
        print('a'+str(index)+'.jpg' + "不存在")
        return
    
    # 获取图像分辨率信息
    dpi = get_image_resolution(image_path)
    
    # 设置分辨率阈值，例如低于100 dpi的图像认为是低分辨率图像
    resolution_threshold = 100
    
    # 创建 ImageStatus 对象
    image_status = ImageStatus(image_path)
    
    # 如果分辨率低于阈值，将状态设置为"转人工"
    if dpi[0] < resolution_threshold or dpi[1] < resolution_threshold:
        print(f"低分辨率图像: {image_path}，分辨率: {dpi}")
        image_status.status = "转人工"
        return image_status

    # 加载图像
    image = Image.open(image_path)
    image = rotate_image_to_normal(image)
    
    ocr = CnOcr()
    out = ocr.ocr(image_path)
    payer = '浙江大学'
 
    invoice = Invoice()
    
    # 标记是否成功识别信息, 0 表示未识别出任何信息，当大于等于 THRESHOLD 时表示识别成功
    info_detected = 0
    THRESHOLD = 5
    total_text_length = 0  # 用于存储所有item的text的总长度
    
    for i, item in enumerate(out):
        text = item['text']
        total_text_length += len(text)  # 累加所有item的text长度

        # 读取付款人
        # 如果当前内容和'浙江大学'至少有四个字符相同，则可认定他们相同
        if len(set(text) & set(payer)) >= 4:
            invoice.payer = payer
            info_detected += 1
        # 读取日期
        # 如果当前内容是是开票日期，则下一个大概率是日期
        if '开票日期' in text:
            if isDate(out[i + 1]['text']):
                invoice.date = out[i + 1]['text']
                info_detected += 1
        # 如果当前内容包含2015年，则这个是日期
        if '2015年' in text:
            substring = '2015年'
            index = text.find(substring)
            if index != -1:
                substring_after = text[index + len(substring):]
            invoice.date = substring + substring_after
            info_detected += 1
        # 如果当前内容符合日期格式，则这个是日期
        if isDate(text):
            invoice.date = text
            info_detected += 1
        # 读取金额
        # 如果当前内容包含小写
        if '小写' in text:
            # 如果当前内容包含 . 则说明小写和金额在同一个内容里
            if '.' in text:
                substring = '小写'
                index = text.find(substring)
                if index != -1:
                    substring_after = text[index + 4:]
                invoice.money = substring_after
                info_detected += 1
            # 如果当前内容不含 . 则在当前内容的后四个内容里找含 . 的内容
            else:
                for j in range(4):
                    tmp = str(out[i + j]['text'])
                    if '.' in tmp:
                        if tmp[0].isdigit():
                            invoice.money = tmp
                        else:
                            invoice.money = tmp[1:]
                        info_detected += 1
                        
        # 判断是否包含关键词
        keywords = ["合同", "甲方", "车号", "里程", "学网", "大巴", "预算", "行程", "上车", "下车"]
        if any(keyword in text for keyword in keywords):
            info_detected -= 1

    # 判断所有item的text的总长度是否太少
    if total_text_length <= 10:  # 这里假设总长度少于等于10就认为太少
        info_detected -= 1
    
    # 如果没有识别出任何信息，将状态设置为"不通过"
    if info_detected < 0:
        image_status.status = "不通过"
        
    if info_detected >= 0 and info_detected < THRESHOLD:
        image_status.status = "转人工"
    
    if info_detected == THRESHOLD:
            image_status.status = "通过"
        
    print(invoice.payer, invoice.date, invoice.money, image_status.status)
    return image_status


# 把所有的a组图片都识别一次，输出结果
# 在循环中统计通过、不通过和转人工的数量
success_num = 0
manual_num = 0
fail_num = 0
max_num = 336
index = 0
while index <= max_num:
    # if index % 10 == 6:
    #     index += 1
    #     continue
    print(index, ' ')
    
    # 调用 ocr_getinfo 函数获取 ImageStatus 对象
    image_status = ocr_getinfo(index)
    
    if image_status is None:
        index += 1
        continue
    # 根据状态进行统计
    if image_status.status == "通过":
        success_num += 1
    elif image_status.status == "不通过":
        fail_num += 1
    elif image_status.status == "转人工":
        manual_num += 1
    
    index += 1

# 打印统计结果
print("通过数量:", success_num)
print("不通过数量:", fail_num)
print("转人工数量:", manual_num)


def ocr_getinfo_test(index):
    # 检查image_path是否存在
    image_path = 'C://Users//Martin//Desktop//FP_dataset//a//a'+str(index)+'.jpg'
    if not os.path.exists(image_path):
        print('a'+str(index)+'.jpg' + "不存在")
        return
    
    # 获取图像分辨率信息
    dpi = get_image_resolution(image_path)
    
    # 设置分辨率阈值，例如低于100 dpi的图像认为是低分辨率图像
    resolution_threshold = 100
    
    # 创建 ImageStatus 对象
    image_status = ImageStatus(image_path)
    
    # 如果分辨率低于阈值，将状态设置为"转人工"
    if dpi[0] < resolution_threshold or dpi[1] < resolution_threshold:
        print(f"低分辨率图像: {image_path}，分辨率: {dpi}")
        image_status.status = "转人工"
        return image_status

    # 加载图像
    image = Image.open(image_path)
    image = rotate_image_to_normal(image)
    
    ocr = CnOcr()
    out = ocr.ocr(image_path)
    payer = '浙江大学'
 
    invoice = Invoice()
    
    # 标记是否成功识别信息, 0 表示未识别出任何信息，当大于等于 THRESHOLD 时表示识别成功
    info_detected = 0
    THRESHOLD = 5
    total_text_length = 0  # 用于存储所有item的text的总长度
    
    for i, item in enumerate(out):
        text = item['text']
        total_text_length += len(text)  # 累加所有item的text长度

        # 读取付款人
        # 如果当前内容和'浙江大学'至少有四个字符相同，则可认定他们相同
        if len(set(text) & set(payer)) >= 4:
            invoice.payer = payer
            info_detected += 1
        # 读取日期
        # 如果当前内容是是开票日期，则下一个大概率是日期
        if '开票日期' in text:
            if isDate(out[i + 1]['text']):
                invoice.date = out[i + 1]['text']
                info_detected += 1
        # 如果当前内容包含2015年，则这个是日期
        if '2015年' in text:
            substring = '2015年'
            index = text.find(substring)
            if index != -1:
                substring_after = text[index + len(substring):]
            invoice.date = substring + substring_after
            info_detected += 1
        # 如果当前内容符合日期格式，则这个是日期
        if isDate(text):
            invoice.date = text
            info_detected += 1
        # 读取金额
        # 如果当前内容包含小写
        if '小写' in text:
            # 如果当前内容包含 . 则说明小写和金额在同一个内容里
            if '.' in text:
                substring = '小写'
                index = text.find(substring)
                if index != -1:
                    substring_after = text[index + 4:]
                invoice.money = substring_after
                info_detected += 1
            # 如果当前内容不含 . 则在当前内容的后四个内容里找含 . 的内容
            else:
                for j in range(4):
                    tmp = str(out[i + j]['text'])
                    if '.' in tmp:
                        if tmp[0].isdigit():
                            invoice.money = tmp
                        else:
                            invoice.money = tmp[1:]
                        info_detected += 1
                        
        # 判断是否包含关键词
        keywords = ["合同", "甲方", "车号", "里程", "学网", "大巴", "预算", "行程", "上车", "下车", "出访任务"]
        if any(keyword in text for keyword in keywords):
            info_detected -= 1
        # print(i, text)


    # 判断所有item的text的总长度是否太少
    if total_text_length <= 10:  # 这里假设总长度少于等于10就认为太少
        info_detected -= 1
    # print("total_text_length"+str(total_text_length))
    # 如果没有识别出任何信息，将状态设置为"不通过"
    if info_detected < 0:
        image_status.status = "不通过"
        
    if info_detected >= 0 and info_detected < THRESHOLD:
        image_status.status = "转人工"
    
    if info_detected == THRESHOLD:
            image_status.status = "通过"
    
    print(invoice.payer, invoice.date, invoice.money, image_status.status)
    return image_status

    ocr_getinfo_test(27)