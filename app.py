import gradio as gr
import tempfile
import math
import hashlib
import base64
import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

class SealGenerator:
    def __init__(self, private_key=None):
        self.private_key = private_key or ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        
    def create_seal(self, company_name, bottom_text, size=400):
        """创建印章核心方法（使用sealGenerate.py方式）"""
        # 根据尺寸计算参数
        R = int(size * 0.6)  # 外圆半径
        H = int(size * 0.3)  # 圆心到中层文字距离
        r = int(size * 0.2)  # 五角星半径
        
        stamp = Stamp(
            R=R,
            H=H,
            r=r,
            edge=int(size*0.05),
            border=int(size*0.03),
            fill=(220, 20, 20, 180),
            words_up=company_name,
            words_mid="",
            words_down=bottom_text,
            angle_up=270,
            angle_down=60,
            font_size_up=int(size*0.12),
            font_size_down=int(size*0.06),
            save_path="temp.png"
        )
        stamp.draw_stamp()
        return stamp.img

    def add_watermark(self, image, data):
        """添加数字水印"""
        signature = self._generate_signature(json.dumps(data))
        watermark = {
            "data": data,
            "signature": signature,
            "public_key": self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
        }
        return self._embed_watermark(image, watermark)

    def _generate_signature(self, data):
        """生成数字签名"""
        signature = self.private_key.sign(
            data.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return base64.b64encode(signature).decode()

    def _embed_watermark(self, image, watermark):
        """嵌入水印到图片"""
        pixels = list(image.getdata())
        watermark_str = json.dumps(watermark)
        watermark_bytes = watermark_str.encode()
        
        # 在前32个像素存储数据长度
        length = len(watermark_bytes)
        for i in range(32):
            if i < len(pixels):
                r, g, b, a = pixels[i]
                r = (r & 0xFE) | ((length >> i) & 1)
                pixels[i] = (r, g, b, a)
        
        # 嵌入水印数据
        bit_index = 0
        for byte in watermark_bytes:
            for bit_pos in range(8):
                pixel_index = 32 + bit_index // 3
                if pixel_index >= len(pixels):
                    break
                
                channel = bit_index % 3
                bit = (byte >> bit_pos) & 1
                
                r, g, b, a = pixels[pixel_index]
                if channel == 0:
                    r = (r & 0xFE) | bit
                elif channel == 1:
                    g = (g & 0xFE) | bit
                else:
                    b = (b & 0xFE) | bit
                
                pixels[pixel_index] = (r, g, b, a)
                bit_index += 1
        
        image.putdata(pixels)
        return image

def generate_seal_interface(company_name, bottom_text, size, key_file):
    """生成印章界面函数"""
    # 初始化生成器
    if key_file:
        with open(key_file.name, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        generator = SealGenerator(private_key)
    else:
        generator = SealGenerator()
    
    # 生成印章
    img = generator.create_seal(company_name, bottom_text, int(size))
    
    # 添加水印
    watermark_data = {
        "company": company_name,
        "timestamp": "2025-08-20",
        "issuer": "红章管理系统"
    }
    img = generator.add_watermark(img, watermark_data)
    
    # 保存临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(temp_file.name)
    return temp_file.name

def verify_seal_interface(image, original_text):
    """验证红章完整性"""
    try:
        img = Image.open(image.name)
        pixels = list(img.getdata())
        
        # 提取水印长度
        length = 0
        for i in range(32):
            if i < len(pixels):
                length |= (pixels[i][0] & 1) << i
        
        # 提取水印数据
        watermark_bytes = bytearray()
        bit_index = 0
        for _ in range(length * 8):
            pixel_index = 32 + bit_index // 3
            if pixel_index >= len(pixels):
                break
            
            channel = bit_index % 3
            r, g, b, a = pixels[pixel_index]
            
            bit = 0
            if channel == 0:
                bit = r & 1
            elif channel == 1:
                bit = g & 1
            else:
                bit = b & 1
                
            if bit_index % 8 == 0:
                watermark_bytes.append(0)
            watermark_bytes[-1] |= (bit << (bit_index % 8))
            bit_index += 1
        
        watermark = json.loads(watermark_bytes.decode())
        public_key = serialization.load_pem_public_key(
            watermark['public_key'].encode()
        )
        
        # 验证签名
        data = json.dumps(watermark['data'], sort_keys=True)
        signature = base64.b64decode(watermark['signature'])
        try:
            public_key.verify(
                signature,
                data.encode(),
                ec.ECDSA(hashes.SHA256())
            )
            return "验证结果：通过\n数据完整性验证成功"
        except:
            return "验证结果：未通过\n数字签名无效"
            
    except Exception as e:
        return f"验证过程中发生错误：{str(e)}"

with gr.Blocks(title="红章生成与验证系统") as demo:
    gr.Markdown("# 🏮 红章管理系统")
    
    with gr.Tabs():
        with gr.TabItem("生成红章"):
            with gr.Row():
                with gr.Column():
                    company_input = gr.Textbox(label="单位名称", placeholder="输入单位名称")
                    bottom_text_input = gr.Textbox(label="底部文字", placeholder="输入底部文字") 
                    size_input = gr.Dropdown(choices=["200", "300", "400"], value="300", label="印章尺寸")
                    key_file = gr.File(label="上传私钥文件（可选）", file_types=[".pem"])
                    generate_btn = gr.Button("生成印章")
                    gr.Markdown("### 密钥管理")
                    generate_key_btn = gr.Button("生成新密钥对")
                    key_output = gr.File(label="下载密钥对", visible=False)
                with gr.Column():
                    output_image = gr.Image(label="生成结果", width=500)

            generate_btn.click(
                fn=generate_seal_interface,
                inputs=[company_input, bottom_text_input, size_input, key_file],
                outputs=output_image
            )
            
            def generate_keys():
                """生成新密钥对"""
                private_key = ec.generate_private_key(ec.SECP256R1())
                public_key = private_key.public_key()
                
                # 保存临时文件
                priv_file = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
                priv_file.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
                priv_file.close()
                
                pub_file = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
                pub_file.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
                pub_file.close()
                
                return [priv_file.name, pub_file.name]
            
            generate_key_btn.click(
                fn=generate_keys,
                outputs=key_output
            )

        with gr.TabItem("验证红章"):
            with gr.Row():
                with gr.Column():
                    upload_image = gr.File(label="上传印章图片", file_types=[".png", ".jpg"])
                    original_text_input = gr.Textbox(label="原始文本", placeholder="输入原始比对文本")
                    verify_btn = gr.Button("开始验证")
                with gr.Column():
                    verify_output = gr.Textbox(label="验证结果", interactive=False)

            verify_btn.click(
                fn=verify_seal_interface,
                inputs=[upload_image, original_text_input],
                outputs=verify_output
            )

if __name__ == "__main__":
    demo.launch()
