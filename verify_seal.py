#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
红章验证工具 - 验证红章的数字签名和完整性
"""

import sys
import json
from PIL import Image
from red_seal_generator import RedSealGenerator

def verify_seal_file(image_path):
    """
    验证红章文件的完整性
    
    Args:
        image_path (str): 红章图片路径
    """
    try:
        # 加载图片
        image = Image.open(image_path)
        print(f"📁 正在验证文件: {image_path}")
        print(f"📏 图片尺寸: {image.size}")
        print(f"🎨 图片模式: {image.mode}")
        
        # 创建生成器（用于验证功能）
        generator = RedSealGenerator()
        
        # 提取签名信息
        print("\n🔍 正在提取数字签名...")
        signature_info = generator.extract_signature_from_image(image)
        
        if not signature_info:
            print("❌ 无法提取签名信息")
            print("   可能原因:")
            print("   - 图片不包含数字签名")
            print("   - 图片已被篡改")
            print("   - 图片格式不支持")
            return False
        
        print("✅ 成功提取签名信息")
        
        # 显示水印数据
        print("\n📋 水印数据:")
        for key, value in signature_info['data'].items():
            print(f"   {key}: {value}")
        
        # 验证签名
        print("\n🔐 正在验证数字签名...")
        data_to_verify = json.dumps(signature_info['data'], sort_keys=True, ensure_ascii=False)
        
        # 注意：这里使用提取出的公钥进行验证
        # 在实际应用中，应该使用预先保存的可信公钥
        try:
            from cryptography.hazmat.primitives import serialization
            public_key_pem = signature_info['public_key']
            public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
            
            # 创建临时生成器来使用提取的公钥
            temp_generator = RedSealGenerator()
            temp_generator.public_key = public_key
            
            is_valid = temp_generator.verify_signature(data_to_verify, signature_info['signature'])
            
            if is_valid:
                print("✅ 数字签名验证通过")
                print("✅ 红章完整性确认")
                print("✅ 数据未被篡改")
                return True
            else:
                print("❌ 数字签名验证失败")
                print("❌ 红章可能已被篡改")
                return False
                
        except Exception as e:
            print(f"❌ 签名验证过程出错: {e}")
            return False
            
    except FileNotFoundError:
        print(f"❌ 文件不存在: {image_path}")
        return False
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False

def main():
    """主函数"""
    print("🔴 红章验证工具")
    print("=" * 50)
    
    if len(sys.argv) != 2:
        print("使用方法: python3 verify_seal.py <红章图片路径>")
        print("\n示例:")
        print("  python3 verify_seal.py red_seal_with_signature.png")
        print("  python3 verify_seal.py custom_seal.png")
        return
    
    image_path = sys.argv[1]
    
    # 验证红章
    is_valid = verify_seal_file(image_path)
    
    print("\n" + "=" * 50)
    if is_valid:
        print("🎉 验证结果: 红章有效且完整")
    else:
        print("⚠️  验证结果: 红章无效或已被篡改")

if __name__ == "__main__":
    main()