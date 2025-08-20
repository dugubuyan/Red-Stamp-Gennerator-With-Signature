import gradio as gr
import red_seal_generator
import verify_seal
import tempfile

def generate_seal_interface(company_name, size, seal_color, text_color):
    """生成红章的界面函数"""
    size = int(size)
    # 生成图片并保存到临时文件
    img = generate_red_seal(company_name, size, seal_color, text_color)
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(temp_file.name)
    return temp_file.name

def verify_seal_interface(image, original_text):
    """验证红章的界面函数"""
    result, confidence = verify_seal.verify_seal_file(image.name, original_text)
    return f"验证结果：{'通过' if result else '未通过'}\n置信度：{confidence:.2%}"

with gr.Blocks(title="红章生成与验证系统") as demo:
    gr.Markdown("# 🏮 红章管理系统")
    
    with gr.Tabs():
        with gr.TabItem("生成红章"):
            with gr.Row():
                with gr.Column():
                    company_input = gr.Textbox(label="单位名称", placeholder="输入单位名称")
                    size_input = gr.Dropdown(choices=["200", "300", "400"], value="300", label="印章尺寸")
                    seal_color = gr.ColorPicker(label="印章颜色", value="#ff0000")
                    text_color = gr.ColorPicker(label="文字颜色", value="#ffffff")
                    generate_btn = gr.Button("生成印章")
                with gr.Column():
                    output_image = gr.Image(label="生成结果", width=500)

            generate_btn.click(
                fn=generate_seal_interface,
                inputs=[company_input, size_input, seal_color, text_color],
                outputs=output_image
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
