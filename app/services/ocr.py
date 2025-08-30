import pytesseract
from PIL import Image
import re
import requests
import io
from app.models.fund import Fund
from app import db

class OCRService:
    @staticmethod
    def extract_text_from_image(image_data):
        """从图片中提取文本"""
        try:
            # 打开图片
            image = Image.open(io.BytesIO(image_data))
            
            # 使用Tesseract OCR提取文本
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            return text
        except Exception as e:
            print(f"OCR识别失败: {e}")
            return None
    
    @staticmethod
    def extract_fund_info_from_text(text):
        """从文本中提取基金信息"""
        if not text:
            return None
        
        # 尝试提取基金代码（6位数字）
        fund_code_match = re.search(r'\b\d{6}\b', text)
        fund_code = fund_code_match.group(0) if fund_code_match else None
        
        # 尝试提取基金名称（通常包含'基金'字样）
        fund_name_patterns = [
            r'[\u4e00-\u9fa5]{2,10}基金',  # 中文基金名称
            r'[\u4e00-\u9fa5]{2,10}[A-Z]{1,4}基金',  # 包含英文后缀的基金名称
        ]
        
        fund_name = None
        for pattern in fund_name_patterns:
            match = re.search(pattern, text)
            if match:
                fund_name = match.group(0)
                break
        
        # 如果只提取到基金代码，可以尝试通过代码查询基金名称
        if fund_code and not fund_name:
            fund = Fund.query.filter_by(code=fund_code).first()
            if fund:
                fund_name = fund.name
        
        return {
            'code': fund_code,
            'name': fund_name
        }
    
    @staticmethod
    def get_fund_info_from_image(image_data):
        """从图片中获取基金信息"""
        # 提取文本
        text = OCRService.extract_text_from_image(image_data)
        if not text:
            return None
        
        # 提取基金信息
        fund_info = OCRService.extract_fund_info_from_text(text)
        
        return fund_info