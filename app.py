# type: ignore
import gradio as gr
import tempfile
import math
import hashlib
import base64
import json
import os
# type: ignore
from PIL import Image, ImageDraw, ImageFont, ImageFilter
# type: ignore
from cryptography.hazmat.primitives import hashes
# type: ignore
from cryptography.hazmat.primitives.asymmetric import ec
# type: ignore
from cryptography.hazmat.primitives import serialization
from math import pi, cos, sin, tan
from random import randint

# 判断字符是否为中文
def is_Chinese(ch):
    if '\u4e00' <= ch <= '\u9fff':
        return True
    return False

# 计算五角星各个顶点
# int R:五角星的长轴
# int x, y:五角星的中心点
# int yDegree:长轴与y轴的夹角
def pentagram(x, y, R, yDegree=0):
    rad = pi / 180  # 每度的弧度值
    r = R * sin(18 * rad) / cos(36 * rad)  # 五角星短轴的长度

    # 求取外圈点坐标
    RVertex = [(x - (R * cos((90 + k * 72 + yDegree) * rad)), y - (R * sin((90 + k * 72 + yDegree) * rad))) for k in
               range(5)]
    # 求取内圈点坐标
    rVertex = [(x - (r * cos((90 + 36 + k * 72 + yDegree) * rad)), y - (r * sin((90 + 36 + k * 72 + yDegree) * rad)))
               for k in range(5)]

    # 顶点左边交叉合并
    vertex = [x for y in zip(RVertex, rVertex) for x in y]
    return vertex

# 计算圆的上下左右切点
def circle(x, y, r):
    return (x - r, y - r, x + r, y + r)

class Stamp:
    def __init__(self, edge=5,  # 图片边缘空白的距离
                 H=160,  # 圆心到中层文字下边缘的距离
                 R=250,  # 圆半径
                 border=20,  # 字到圆圈内侧的距离
                 r=90,  # 五星外接圆半径
                 fill=(255, 0, 0, 120),  # 印章颜色， 默认纯红色， 透明度0-255，建议90-180

                 words_up="上海市一个好鸟都没有有限公司",  # 上部文字
                 angle_up=270,  # 上部文字弧形角度
                 font_size_up=80,  # 上部文字大小
                 font_xratio_up=0.66,  # 上部文字横向变形比例
                 stroke_width_up=2,  # 上部文字粗细，一般取值0,1,2,3

                 words_mid="测试专用章",  # 中部文字
                 angle_mid=72,  # 中部文字弧形角度
                 font_size_mid=60,  # 中部文字大小
                 font_xratio_mid=0.7,  # 中部文字横向变形比例
                 stroke_width_mid=1,  # 中部文字粗细，一般取值0,1,2

                 words_down="0123456789",  # 下部文字
                 angle_down=60,  # 下部文字弧形角度
                 font_size_down=20,  # 下部文字大小
                 font_xratio_down=1,  # 下部文字横向变形比例
                 stroke_width_down=1,  # 下部文字粗细，一般取值0,1,2

                 save_path="stamp.png"  # 保存图片路径
                 ):

        # 图像初始设置为None
        self.img = None
        self.save_path = save_path

        self.fill = fill  # 印章颜色
        self.edge = edge  # 图片边缘空白的距离
        self.H = H  # 圆心到中层文字下边缘的距离
        self.R = R  # 圆半径
        self.r = r  # 五星外接圆半径
        self.border = border  # 字到圆圈内侧的距离

        self.words_up = words_up  # 上部文字
        self.angle_up = angle_up  # 上部文字弧形角度
        self.font_size_up = font_size_up  # 上部文字大小
        self.font_xratio_up = font_xratio_up  # 上部文字横向变形比例
        self.stroke_width_up = stroke_width_up  # 上部文字粗细，一般取值0,1,2,3

        self.words_mid = words_mid  # 中部文字
        self.angle_mid = angle_mid  # 中部文字弧形角度
        self.font_size_mid = font_size_mid  # 中部文字大小
        self.font_xratio_mid = font_xratio_mid  # 中部文字横向变形比例
        self.stroke_width_mid = stroke_width_mid  # 中部文字粗细，一般取值0,1,2,3

        self.words_down = words_down  # 下部文字
        self.angle_down = angle_down  # 下部文字弧形角度
        self.font_size_down = font_size_down  # 下部文字大小
        self.font_xratio_down = font_xratio_down  # 下部文字横向变形比例
        self.stroke_width_down = stroke_width_down  # 中部文字粗细，一般取值0,1,2,3

    def draw_rotated_text(self, image, angle, xy, r, word, fill, font_size, font_xratio, stroke_width, font_flip=False,
                          *args, **kwargs):
        """
            image:底层图片
            angle：旋转角度
            xy：旋转中心
            r:旋转半径
            text：绘制的文字
            fill：文字颜色
            font_size：字体大小
            font_xratio：x方向缩放比例（印章字体宽度较标准宋体偏窄）
            stroke_width： 文字笔画粗细
            font_flip:文字是否垂直翻转（印章下部文字与上部是相反的）
        """

        # 加载字体文件-直接使用windows自带字体，中文用simsun， 英文用arial
        if is_Chinese(word):
            font = ImageFont.truetype("SIMSUN.ttf", font_size, encoding="utf-8")
        else:
            font = ImageFont.truetype("arialr.ttf", font_size, encoding="utf-8")

        # 获取底层图片的size
        width, height = image.size
        max_dim = max(width, height)

        # 创建透明背景的文字层，大小4倍的底层图片
        mask_size = (max_dim * 2, max_dim * 2)
        # 印章通常使用较窄的字体，这里将绘制文字的图层x方向压缩到font_xratio的比例
        mask_resize = (int(max_dim * 2 * font_xratio), max_dim * 2)
        mask = Image.new('L', mask_size, 0)

        # 在上面文字层的中心处写字，字的左上角与中心对其
        draw = ImageDraw.Draw(mask)

        # 获取当前设置字体的宽高
        bd = draw.textbbox((max_dim, max_dim), word, font=font, align="center", *args, **kwargs)
        font_width = bd[2] - bd[0]
        font_hight = bd[3] - bd[1]

        # 文字在圆圈上下的方向，需要通过文字所在文字图层的位置修正，保证所看到的文字不会上下颠倒
        if font_flip:
            word_pos = (int(max_dim - font_width / 2), max_dim + r - font_hight)
        else:
            word_pos = (int(max_dim - font_width / 2), max_dim - r)

        # 写字， 以xy为中心，r为半径，文字上边中点为圆周点，绘制文字
        draw.text(word_pos, word, 255, font=font, align="center", stroke_width=stroke_width, *args, **kwargs)

        # 调整角度,对于Π*n/2的角度，直接rotate即可，对于非Π*n/2的角度，需要先放大图片以减少旋转带来的锯齿
        if angle % 90 == 0:
            rotated_mask = mask.resize(mask_resize).rotate(angle)
        else:
            bigger_mask = mask.resize((int(max_dim * 8 * font_xratio), max_dim * 8),
                                      resample=Image.BICUBIC)
            rotated_mask = bigger_mask.rotate(angle).resize(mask_resize, resample=Image.LANCZOS)

        # 切割文字的图片
        mask_xy = (max_dim * font_xratio - xy[0], max_dim - xy[1])
        b_box = mask_xy + (mask_xy[0] + width, mask_xy[1] + height)
        mask = rotated_mask.crop(b_box)

        # 粘贴到目标图片上
        color_image = Image.new('RGBA', image.size, fill)
        image.paste(color_image, mask)

    def draw_stamp(self):
        # 创建一张底图,用来绘制文字
        img = Image.new("RGBA", (2 * (self.R + self.edge), 2 * (self.R + self.edge)), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        # 绘制圆弧， R为外边缘，width往圆心算
        draw.arc(circle(self.R + self.edge, self.R + self.edge, self.R), start=0, end=360, fill=self.fill,
                 width=self.border)

        # 绘制多边形
        draw.polygon(pentagram(self.R + self.edge, self.R + self.edge, self.r), fill=self.fill, outline=self.fill)

        # 绘制上圈文字
        angle_word = self.angle_up / len(self.words_up)
        angle_word_curr = ((len(self.words_up) - 1) / 2) * angle_word

        for word in self.words_up:
            self.draw_rotated_text(img, angle_word_curr, (self.R + self.edge, self.R + self.edge),
                                   self.R - self.border * 2,
                                   word, self.fill, self.font_size_up, self.font_xratio_up, self.stroke_width_up)
            angle_word_curr = angle_word_curr - angle_word

        # 绘制中层文字（当有内容时）
        if self.words_mid:
            angle_word = self.angle_mid / len(self.words_mid)
            angle_word_curr = -((len(self.words_mid) - 1) / 2) * angle_word

            for word in self.words_mid:
                self.draw_rotated_text(img, 0,
                                      (self.R + self.edge + self.H * tan(angle_word_curr * pi / 180), self.R + self.edge),
                                      self.H,
                                      word, self.fill, self.font_size_mid, self.font_xratio_mid, self.stroke_width_mid,
                                      font_flip=True)
                angle_word_curr = angle_word_curr + angle_word
            angle_word_curr = angle_word_curr + angle_word

        # 绘制下圈文字
        angle_word = self.angle_down / len(self.words_down)
        angle_word_curr = -((len(self.words_down) - 1) / 2) * angle_word

        for word in self.words_down:
            self.draw_rotated_text(img, angle_word_curr, (self.R + self.edge, self.R + self.edge),
                                   self.R - self.border * 2,
                                   word, self.fill, self.font_size_down, self.font_xratio_down, self.stroke_width_down,
                                   font_flip=True)
            angle_word_curr = angle_word_curr + angle_word

        self.img = img.filter(ImageFilter.GaussianBlur(0.6))

    def show_stamp(self):
        if self.img:
            self.img.show()

    def save_stamp(self):
        if self.img:
            self.img.save(self.save_path)

class SealGenerator:
    def __init__(self, private_key=None):
        self.private_key = private_key or ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        
    def create_seal(self, company_name, bottom_text, size=400):
        """创建印章核心方法（使用sealGenerate.py方式）"""
        # 根据尺寸计算参数
        R = int(size * 0.65)  # 外圆半径
        H = int(size * 0.25)  # 圆心到中层文字距离
        r = int(size * 0.25)  # 五角星半径
        
        stamp = Stamp(
            R=R,
            H=H,
            r=r,
            edge=int(size*0.04),
            border=int(size*0.04),
            fill=(220, 20, 20, 180),
            words_up=company_name,
            words_mid="",
            words_down=bottom_text,
            angle_up=270,
            angle_down=60,
            font_size_up=int(size*0.2),
            font_size_down=int(size*0.1),
            save_path="temp.png"
        )
        stamp.draw_stamp()
        return stamp.img

    def add_watermark(self, image, data):
        """添加数字水印"""
        signature = self._generate_signature(json.dumps(data, sort_keys=True))
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

def generate_seal_interface(company_name, bottom_text, size, enable_watermark, watermark_file, key_file):
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
    
    watermark_data = None
    if enable_watermark:
        # 处理签名文件
        content = b""
        content_type = "file"
        if watermark_file:
            try:
                with open(watermark_file.name, "rb") as f:
                    content = f.read()
            except Exception as e:
                # 先保存临时文件再返回
                temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                if img is not None:  # 确保img不是None
                    img.save(temp_file.name)
                return temp_file.name, {"error": f"文件读取失败: {str(e)}"}
        
        if content:
            # 计算内容哈希
            content_hash = hashlib.sha256(content.encode() if isinstance(content, str) else content).hexdigest()
            
            # 构建水印数据
            watermark_data = {
                "issuer": company_name,
                "timestamp": "2025-08-20",
                "file_hash": content_hash,
                "file_size": len(content)
            }
            img = generator.add_watermark(img, watermark_data)
        else:
            watermark_data = {"error": "未提供水印内容"}
    
    # 保存临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    if img is not None:  # 确保img不是None
        img.save(temp_file.name)
    return temp_file.name, watermark_data if watermark_data else {}

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
                    
                    enable_watermark = gr.Checkbox(label="启用签名数字水印", value=False)
                    watermark_acc = gr.Group(visible=False)
                    
                    # 添加类名以便JavaScript选择
                    watermark_acc.elem_classes = ["watermark-group"]
                    
                    with watermark_acc:
                        watermark_file = gr.File(label="上传欲签名文件", file_types=[".txt", ".pdf", ".docx"])
                        key_file = gr.File(label="私钥文件", file_types=[".pem"])
                        gr.Markdown("### 密钥管理")
                        generate_key_btn = gr.Button("生成新密钥对")
                        key_output = gr.File(label="下载私钥文件", visible=True)
                    
                    generate_btn = gr.Button("生成印章")
                with gr.Column():
                    output_image = gr.Image(label="生成结果", width=500)
                    watermark_output = gr.JSON(label="水印数据", visible=False, elem_classes=["watermark-output"])
                    
                    # 使用Python函数处理组件可见性
                    def update_visibility(x):
                        return gr.Group(visible=x), gr.JSON(visible=x)
                    
                    # 添加事件处理
                    enable_watermark.change(
                        fn=update_visibility,
                        inputs=[enable_watermark],
                        outputs=[watermark_acc, watermark_output]
                    )

            generate_btn.click(
                fn=generate_seal_interface,
                inputs=[company_input, bottom_text_input, size_input, enable_watermark, watermark_file, key_file],
                outputs=[output_image, watermark_output]
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
                
                # 生成并返回公钥文件路径
                pub_file = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
                pub_file.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
                pub_file.close()
                
                # 返回私钥文件路径到下载和上传组件
                return priv_file.name, priv_file.name
            
            generate_key_btn.click(
                fn=generate_keys,
                outputs=[key_output, key_file]
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
    demo.launch(mcp_server=True)
