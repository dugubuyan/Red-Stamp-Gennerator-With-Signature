#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
红章生成器 - 生成带数字签名水印的红章
"""

from PIL import Image, ImageDraw, ImageFont
import math
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64
import json
import os

class RedSealGenerator:
    def __init__(self, size=400):
        """
        初始化红章生成器
        
        Args:
            size (int): 红章尺寸，默认400像素
        """
        self.size = size
        self.center = size // 2
        self.outer_radius = size // 2 - 20
        self.inner_radius = size // 2 - 40
        self.star_radius = 80
        
        # 生成ECDSA密钥对
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
    
    def create_red_seal(self, company_name="测试单位印章", serial_number="0123456789", ultra_smooth=True):
        """
        创建红章图片
        
        Args:
            company_name (str): 公司名称
            serial_number (str): 印章编号
            ultra_smooth (bool): 是否使用超级抗锯齿模式
            
        Returns:
            PIL.Image: 红章图片
        """
        if ultra_smooth:
            return self._create_ultra_smooth_seal(company_name, serial_number)
        else:
            return self._create_standard_seal(company_name, serial_number)
    
    def _create_ultra_smooth_seal(self, company_name, serial_number):
        """创建超级光滑的红章"""
        # 使用8倍超采样获得更好的抗锯齿效果
        scale_factor = 8
        high_res_size = self.size * scale_factor
        high_res_center = high_res_size // 2
        high_res_outer_radius = self.outer_radius * scale_factor
        high_res_star_radius = self.star_radius * scale_factor
        
        # 创建超高分辨率透明背景图片
        high_res_img = Image.new('RGBA', (high_res_size, high_res_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(high_res_img)
        
        # 绘制外圆 - 使用多层绘制技术获得更光滑的边缘
        self._draw_smooth_circle(draw, high_res_center, high_res_outer_radius, 
                               6 * scale_factor, (220, 20, 20, 255))

        # 绘制超光滑五角星
        self._draw_smooth_star(draw, high_res_center, high_res_center, 
                             high_res_star_radius, (220, 20, 20, 255))
        
        # 绘制公司名称（圆形排列）- 使用更好的字体渲染
        self._draw_smooth_circular_text(draw, company_name, high_res_center, high_res_center, 
                                      high_res_outer_radius - 30 * scale_factor, 
                                      (220, 20, 20, 255), scale_factor)
        
        # 绘制编号 - 使用更好的字体渲染
        self._draw_smooth_serial_number(draw, serial_number, (220, 20, 20, 255), 
                                      high_res_center, high_res_star_radius, scale_factor)
        
        # 应用轻微的高斯模糊以进一步平滑边缘
        from PIL import ImageFilter
        high_res_img = high_res_img.filter(ImageFilter.GaussianBlur(radius=0.8))
        
        # 使用多步缩放获得最佳质量
        # 先缩放到2倍大小
        mid_size = self.size * 2
        mid_img = high_res_img.resize((mid_size, mid_size), Image.LANCZOS)
        
        # 再缩放到目标尺寸
        final_img = mid_img.resize((self.size, self.size), Image.LANCZOS)
        
        return final_img
    
    def _create_standard_seal(self, company_name, serial_number):
        """创建标准质量的红章（原有实现）"""
        # 创建高分辨率图片用于抗锯齿，然后缩放回目标尺寸
        scale_factor = 4  # 4倍分辨率用于抗锯齿
        high_res_size = self.size * scale_factor
        high_res_center = high_res_size // 2
        high_res_outer_radius = self.outer_radius * scale_factor
        high_res_star_radius = self.star_radius * scale_factor
        
        # 创建高分辨率透明背景图片
        high_res_img = Image.new('RGBA', (high_res_size, high_res_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(high_res_img)
        
        # 绘制外圆 - 使用更粗的线条在高分辨率下
        circle_width = 6 * scale_factor
        draw.ellipse([
            high_res_center - high_res_outer_radius,
            high_res_center - high_res_outer_radius,
            high_res_center + high_res_outer_radius,
            high_res_center + high_res_outer_radius
        ], outline=(220, 20, 20, 255), width=circle_width)
        
        # 绘制五角星
        self._draw_star(draw, high_res_center, high_res_center, high_res_star_radius, (220, 20, 20, 255))
        
        # 绘制公司名称（圆形排列）
        self._draw_circular_text(draw, company_name, high_res_center, high_res_center, 
                                high_res_outer_radius - 30 * scale_factor, (220, 20, 20, 255), scale_factor)
        
        # 绘制编号
        self._draw_serial_number(draw, serial_number, (220, 20, 20, 255), high_res_center, high_res_star_radius, scale_factor)
        
        # 使用高质量重采样缩放回目标尺寸
        img = high_res_img.resize((self.size, self.size), Image.LANCZOS)
        
        return img
    
    def _draw_star(self, draw, cx, cy, radius, color):
        """绘制五角星"""
        points = []
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            if i % 2 == 0:
                r = radius
            else:
                r = radius * 0.4
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        
        draw.polygon(points, fill=color)
    
    def _draw_smooth_circle(self, draw, center, radius, width, color):
        """绘制超光滑圆形 - 使用多层技术"""
        # 绘制多个稍微不同粗细的圆形来创建更光滑的边缘
        for i in range(3):
            alpha_factor = 1.0 - (i * 0.2)  # 逐渐降低透明度
            current_color = (color[0], color[1], color[2], int(color[3] * alpha_factor))
            current_width = width + i
            
            draw.ellipse([
                center - radius,
                center - radius,
                center + radius,
                center + radius
            ], outline=current_color, width=current_width)
            
    def _draw_smooth_star(self, draw, cx, cy, radius, color):
        """绘制超光滑五角星 - 使用抗锯齿技术"""
        # 计算五角星的点，使用更高精度
        points = []
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            if i % 2 == 0:
                r = radius
            else:
                r = radius * 0.4
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        
        # 绘制主体
        draw.polygon(points, fill=color)
        
        # 绘制边缘抗锯齿 - 使用稍微透明的颜色绘制轮廓
        edge_color = (color[0], color[1], color[2], int(color[3] * 0.3))
        draw.polygon(points, outline=edge_color, width=2)
    
    def _draw_circular_text(self, draw, text, cx, cy, radius, color, scale_factor=1):
        """绘制圆形排列的文字"""
        try:
            # 根据缩放因子调整字体大小
            font_size = int(28 * scale_factor)
            font = None
            
            # macOS字体路径
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial Unicode.ttf"
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
            
            if font is None:
                # 如果没有找到TrueType字体，使用默认字体并调整大小
                font = ImageFont.load_default()
                
        except:
            font = ImageFont.load_default()
        
        char_count = len(text)
        if char_count == 0:
            return
            
        # 计算每个字符的角度间隔
        total_angle = math.pi * 1.2  # 约216度
        start_angle = -math.pi * 0.6 - math.pi / 2  # 从顶部开始
        
        for i, char in enumerate(text):
            angle = start_angle + (total_angle * i / (char_count - 1) if char_count > 1 else 0)
            
            # 计算字符位置
            char_x = cx + radius * math.cos(angle)
            char_y = cy + radius * math.sin(angle)
            
            # 获取字符尺寸
            bbox = draw.textbbox((0, 0), char, font=font)
            char_width = bbox[2] - bbox[0]
            char_height = bbox[3] - bbox[1]
            
            # 绘制字符 - 启用抗锯齿
            draw.text((char_x - char_width/2, char_y - char_height/2), 
                     char, fill=color, font=font)
    
    def _draw_serial_number(self, draw, serial_number, color, center, star_radius, scale_factor=1):
        """绘制编号"""
        try:
            font_size = int(16 * scale_factor)  # 根据缩放因子调整字体大小
            font = None
            
            # 尝试使用系统字体
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial Unicode.ttf"
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
            
            if font is None:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # 在底部绘制编号
        bbox = draw.textbbox((0, 0), serial_number, font=font)
        text_width = bbox[2] - bbox[0]
        
        draw.text((center - text_width/2, center + star_radius + 30 * scale_factor), 
                 serial_number, fill=color, font=font)
    
    def _draw_smooth_circular_text(self, draw, text, cx, cy, radius, color, scale_factor=1):
        """绘制超光滑圆形排列的文字"""
        try:
            # 根据缩放因子调整字体大小，并增加一些额外的大小以获得更好的渲染质量
            font_size = int(28 * scale_factor * 1.1)  # 稍微增大字体以获得更好的抗锯齿
            font = None
            
            # macOS字体路径
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/Helvetica.ttc", 
                "/Library/Fonts/Arial Unicode.ttf"
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
            
            if font is None:
                font = ImageFont.load_default()
                
        except:
            font = ImageFont.load_default()
        
        char_count = len(text)
        if char_count == 0:
            return
            
        # 计算每个字符的角度间隔
        total_angle = math.pi * 1.2  # 约216度
        start_angle = -math.pi * 0.6 - math.pi / 2  # 从顶部开始
        
        for i, char in enumerate(text):
            angle = start_angle + (total_angle * i / (char_count - 1) if char_count > 1 else 0)
            
            # 计算字符位置
            char_x = cx + radius * math.cos(angle)
            char_y = cy + radius * math.sin(angle)
            
            # 获取字符尺寸
            bbox = draw.textbbox((0, 0), char, font=font)
            char_width = bbox[2] - bbox[0]
            char_height = bbox[3] - bbox[1]
            
            # 多层绘制文字以获得更好的抗锯齿效果
            # 先绘制稍微透明的阴影
            shadow_color = (color[0], color[1], color[2], int(color[3] * 0.3))
            for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                draw.text((char_x - char_width/2 + dx, char_y - char_height/2 + dy), 
                         char, fill=shadow_color, font=font)
            
            # 绘制主文字
            draw.text((char_x - char_width/2, char_y - char_height/2), 
                     char, fill=color, font=font)
    
    def _draw_smooth_serial_number(self, draw, serial_number, color, center, star_radius, scale_factor=1):
        """绘制超光滑编号"""
        try:
            font_size = int(16 * scale_factor * 1.1)  # 稍微增大字体
            font = None
            
            # 尝试使用系统字体
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial Unicode.ttf"
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
            
            if font is None:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # 在底部绘制编号
        bbox = draw.textbbox((0, 0), serial_number, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = center - text_width/2
        text_y = center + star_radius + 30 * scale_factor
        
        # 多层绘制以获得更好的抗锯齿效果
        # 先绘制稍微透明的阴影
        shadow_color = (color[0], color[1], color[2], int(color[3] * 0.3))
        for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            draw.text((text_x + dx, text_y + dy), serial_number, fill=shadow_color, font=font)
        
        # 绘制主文字
        draw.text((text_x, text_y), serial_number, fill=color, font=font)
    
    def generate_signature(self, data):
        """
        使用ECDSA生成数字签名
        
        Args:
            data (str): 要签名的数据
            
        Returns:
            str: Base64编码的签名
        """
        data_bytes = data.encode('utf-8')
        signature = self.private_key.sign(data_bytes, ec.ECDSA(hashes.SHA256()))
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_signature(self, data, signature_b64):
        """
        验证数字签名
        
        Args:
            data (str): 原始数据
            signature_b64 (str): Base64编码的签名
            
        Returns:
            bool: 验证结果
        """
        try:
            data_bytes = data.encode('utf-8')
            signature = base64.b64decode(signature_b64)
            self.public_key.verify(signature, data_bytes, ec.ECDSA(hashes.SHA256()))
            return True
        except:
            return False
    
    def add_watermark(self, seal_image, watermark_data):
        """
        在红章上添加数字签名水印
        
        Args:
            seal_image (PIL.Image): 红章图片
            watermark_data (dict): 水印数据
            
        Returns:
            PIL.Image: 带水印的红章图片
        """
        # 创建水印图片
        watermark_img = Image.new('RGBA', seal_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_img)
        
        # 生成签名
        data_to_sign = json.dumps(watermark_data, sort_keys=True, ensure_ascii=False)
        signature = self.generate_signature(data_to_sign)
        
        # 在图片底部添加不可见的签名信息
        signature_info = {
            'signature': signature,
            'data': watermark_data,
            'public_key': self.get_public_key_pem()
        }
        
        # 将签名信息编码为像素（隐写术）
        self._embed_signature_in_pixels(seal_image, signature_info)
        
        return seal_image
    
    def _embed_signature_in_pixels(self, image, signature_info):
        """
        将签名信息嵌入到图片像素中（简单的LSB隐写术）
        """
        signature_json = json.dumps(signature_info, ensure_ascii=False)
        signature_bytes = signature_json.encode('utf-8')
        
        # 转换为可修改的图片
        pixels = list(image.getdata())
        
        # 将签名长度信息嵌入前32个像素的最低位
        sig_len = len(signature_bytes)
        for i in range(32):
            if i < len(pixels):
                r, g, b, a = pixels[i]
                # 修改红色通道的最低位
                bit = (sig_len >> i) & 1
                r = (r & 0xFE) | bit
                pixels[i] = (r, g, b, a)
        
        # 将签名数据嵌入后续像素
        bit_index = 0
        for byte in signature_bytes:
            for bit_pos in range(8):
                pixel_index = 32 + bit_index // 3
                if pixel_index >= len(pixels):
                    break
                    
                r, g, b, a = pixels[pixel_index]
                bit = (byte >> bit_pos) & 1
                
                # 根据bit_index % 3决定修改哪个颜色通道
                channel = bit_index % 3
                if channel == 0:
                    r = (r & 0xFE) | bit
                elif channel == 1:
                    g = (g & 0xFE) | bit
                else:
                    b = (b & 0xFE) | bit
                
                pixels[pixel_index] = (r, g, b, a)
                bit_index += 1
        
        # 更新图片
        image.putdata(pixels)
    
    def extract_signature_from_image(self, image):
        """
        从图片中提取签名信息
        
        Args:
            image (PIL.Image): 带签名的图片
            
        Returns:
            dict: 签名信息，如果提取失败返回None
        """
        try:
            pixels = list(image.getdata())
            
            # 提取签名长度
            sig_len = 0
            for i in range(32):
                if i < len(pixels):
                    r, g, b, a = pixels[i]
                    bit = r & 1
                    sig_len |= (bit << i)
            
            if sig_len <= 0 or sig_len > 10000:  # 合理性检查
                return None
            
            # 提取签名数据
            signature_bytes = bytearray()
            bit_index = 0
            current_byte = 0
            bit_in_byte = 0
            
            for _ in range(sig_len * 8):
                pixel_index = 32 + bit_index // 3
                if pixel_index >= len(pixels):
                    break
                
                r, g, b, a = pixels[pixel_index]
                channel = bit_index % 3
                
                if channel == 0:
                    bit = r & 1
                elif channel == 1:
                    bit = g & 1
                else:
                    bit = b & 1
                
                current_byte |= (bit << bit_in_byte)
                bit_in_byte += 1
                
                if bit_in_byte == 8:
                    signature_bytes.append(current_byte)
                    current_byte = 0
                    bit_in_byte = 0
                
                bit_index += 1
            
            # 解码签名信息
            signature_json = signature_bytes.decode('utf-8')
            return json.loads(signature_json)
            
        except Exception as e:
            print(f"提取签名失败: {e}")
            return None
    
    def get_public_key_pem(self):
        """获取公钥的PEM格式"""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def save_keys(self, private_key_file="private_key.pem", public_key_file="public_key.pem"):
        """保存密钥对到文件"""
        # 保存私钥
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with open(private_key_file, 'wb') as f:
            f.write(private_pem)
        
        # 保存公钥
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(public_key_file, 'wb') as f:
            f.write(public_pem)


def main():
    """主函数 - 演示功能"""
    # 创建红章生成器
    generator = RedSealGenerator(size=400)
    
    # 生成红章（默认使用超级抗锯齿模式）
    print("正在生成超级光滑红章...")
    seal = generator.create_red_seal(
        company_name="广东都好测试专用章",
        serial_number="0123456789",
        ultra_smooth=True
    )
    
    # 准备水印数据
    watermark_data = {
        "timestamp": "2025-01-13 10:30:00",
        "document_id": "DOC-2025-001",
        "user": "张三",
        "department": "财务部"
    }
    
    # 添加数字签名水印
    print("正在添加数字签名水印...")
    sealed_image = generator.add_watermark(seal, watermark_data)
    
    # 保存图片
    sealed_image.save("red_seal_with_signature.png")
    print("红章已保存为: red_seal_with_signature.png")
    
    # 保存密钥
    generator.save_keys()
    print("密钥已保存为: private_key.pem 和 public_key.pem")
    
    # 验证签名
    print("\n正在验证数字签名...")
    extracted_info = generator.extract_signature_from_image(sealed_image)
    
    if extracted_info:
        # 验证签名
        data_to_verify = json.dumps(extracted_info['data'], sort_keys=True, ensure_ascii=False)
        is_valid = generator.verify_signature(data_to_verify, extracted_info['signature'])
        
        print(f"签名验证结果: {'有效' if is_valid else '无效'}")
        print(f"水印数据: {extracted_info['data']}")
    else:
        print("无法提取签名信息")


if __name__ == "__main__":
    main()