# 红章生成器 - 超级抗锯齿 + 数字签名防篡改

这是一个Python实现的专业级红章生成器，具有以下特点：
- 生成传统中式红章样式
- **超级抗锯齿技术**：8倍超采样 + 高斯模糊 + 多层渲染
- 使用ECDSA数字签名技术防篡改
- 支持隐写术将签名嵌入图片像素中
- 可验证红章完整性和真实性

## 功能特性

### 🔴 红章绘制
- 圆形边框设计
- 五角星中心图案
- 圆弧排列的公司名称
- 底部编号显示
- 支持自定义尺寸和文字
- **超级抗锯齿优化**: 
  - 标准模式：4倍超采样 + LANCZOS重采样
  - 超级光滑模式：8倍超采样 + 高斯模糊 + 多层渲染 + 多步缩放

### 🔐 数字签名
- 使用ECDSA椭圆曲线数字签名算法
- SHA-256哈希算法
- 生成公私钥对
- 签名验证功能

### 🛡️ 防篡改保护
- LSB隐写术将签名嵌入像素
- 任何像素修改都会导致验证失败
- 支持水印数据完整性检查
- 无法伪造或篡改

## 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install Pillow cryptography
```

## 快速开始

### 基本使用

```python
from red_seal_generator import RedSealGenerator

# 创建生成器
generator = RedSealGenerator(size=400)

# 生成超级光滑红章（推荐，默认模式）
seal = generator.create_red_seal(
    company_name="北京科技有限公司",
    serial_number="1234567890",
    ultra_smooth=True  # 超级抗锯齿模式
)

# 或者使用标准模式（更快速）
seal = generator.create_red_seal(
    company_name="北京科技有限公司",
    serial_number="1234567890", 
    ultra_smooth=False  # 标准抗锯齿模式
)

# 准备水印数据
watermark_data = {
    "document_type": "合同",
    "contract_id": "HT-2025-001",
    "signer": "张经理",
    "timestamp": "2025-01-13 10:30:00"
}

# 添加数字签名水印
signed_seal = generator.add_watermark(seal, watermark_data)

# 保存红章
signed_seal.save("my_seal.png")

# 保存密钥对
generator.save_keys("private.pem", "public.pem")
```

### 验证红章完整性

```python
# 从图片中提取签名信息
signature_info = generator.extract_signature_from_image(signed_seal)

if signature_info:
    # 验证签名
    data_to_verify = json.dumps(signature_info['data'], sort_keys=True, ensure_ascii=False)
    is_valid = generator.verify_signature(data_to_verify, signature_info['signature'])
    
    if is_valid:
        print("✅ 红章验证通过，未被篡改")
        print(f"水印数据: {signature_info['data']}")
    else:
        print("❌ 红章验证失败，可能已被篡改")
else:
    print("❌ 无法提取签名信息")
```

## 运行示例

### 基础示例
```bash
python3 red_seal_generator.py
```

### 验证红章完整性
```bash
python3 verify_seal.py
```

### 超级抗锯齿效果对比
```bash
python3 ultra_smooth_test.py
```

## 生成的文件

运行程序后会生成以下文件：

### 核心文件
- `red_seal_with_signature.png` - 带数字签名的红章
- `private_key.pem` - 私钥文件（用于签名）
- `public_key.pem` - 公钥文件（用于验证）

### 示例文件
- `custom_seal.png` - 自定义红章示例
- `custom_seal_with_signature.png` - 带签名的自定义红章
- `ultra_smooth_seal.png` - 超级光滑红章示例

### 对比文件
- `ultra_comparison.png` - 标准vs超级光滑对比图
- `zoom_comparison.png` - 放大4倍细节对比图

## 技术原理

### 数字签名流程
1. 使用ECDSA算法生成公私钥对
2. 对水印数据进行SHA-256哈希
3. 使用私钥对哈希值进行签名
4. 将签名和数据嵌入到图片像素中

### 隐写术实现
- 使用LSB（最低有效位）隐写术
- 将签名长度信息存储在前32个像素的红色通道最低位
- 将签名数据按位存储在后续像素的RGB通道最低位
- 任何像素修改都会破坏签名完整性

### 验证过程
1. 从图片像素中提取签名信息
2. 重新计算水印数据的哈希值
3. 使用公钥验证签名
4. 比较哈希值确认数据完整性

## 安全特性

- **不可伪造**: 没有私钥无法生成有效签名
- **不可篡改**: 任何像素修改都会导致验证失败
- **不可抵赖**: 签名与私钥唯一对应
- **完整性保护**: 水印数据任何修改都能被检测

## 注意事项

1. **私钥安全**: 私钥文件需要妥善保管，泄露后签名将失去意义
2. **图片格式**: 建议使用PNG格式保存，避免JPEG压缩损失
3. **像素精度**: 不要对签名后的图片进行任何像素级编辑
4. **密钥管理**: 建议为不同用途生成不同的密钥对

## 应用场景

- 电子合同签章
- 公文盖章
- 证书认证
- 文档防伪
- 数字资产保护

## 项目结构

```
红章生成器/
├── red_seal_generator.py      # 核心生成器（主程序）
├── verify_seal.py            # 红章验证工具
├── ultra_smooth_test.py      # 超级抗锯齿测试
├── requirements.txt          # 依赖包列表
├── README.md                # 项目说明
├── 抗锯齿优化说明.md         # 技术详细说明
├── 项目说明.md              # 中文项目说明
└── 生成的文件/
    ├── *.png                # 生成的红章图片
    └── *.pem                # 密钥文件
```

## 抗锯齿技术对比

| 模式 | 超采样 | 高斯模糊 | 多层渲染 | 质量 | 速度 |
|------|--------|----------|----------|------|------|
| 标准模式 | 4倍 | ❌ | ❌ | 好 | 快 |
| 超级光滑 | 8倍 | ✅ | ✅ | 极佳 | 较慢 |

详细技术说明请查看 `抗锯齿优化说明.md`

## 许可证

MIT License - 可自由使用和修改