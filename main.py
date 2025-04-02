from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import gradio as gr
import uvicorn
import time
import re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

from DVC_SearchAssist import DVC_SearchAssist

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

# > http://localhost:5002/?input_text=T%C3%B4i%20mu%E1%BB%91n%20kh%E1%BB%9Fi%20nghi%E1%BB%87p%20th%C3%AC%20c%E1%BA%A7n%20th%E1%BB%A7%20t%E1%BB%A5c%20n%C3%A0o?
@app.get("/")
def myapiyeah(input_text: str = ""):
    return DVC_SearchAssist(input_text)

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================
theme = gr.themes.Base(
    # primary_hue="neutral",
    # secondary_hue="neutral",
    # neutral_hue="neutral",
    font=[gr.themes.GoogleFont('Inter')], 
    font_mono=[gr.themes.GoogleFont('Ubuntu Mono')]
)
head = """
<link rel="icon" href="https://raw.githubusercontent.com/baobuiquang/DVC_SearchAssistant_V2/refs/heads/main/static/logo.png">
"""
css = """
footer, h1 { display: none !important; }
* { -ms-overflow-style: none; scrollbar-width: none; }
*::-webkit-scrollbar { display: none; }
main { margin-bottom: 24px !important; max-width: 900px !important; }
#cmp_chatbot { flex-grow: 1; }
#cmp_textbox textarea { background: transparent !important; }
.message.bot { margin-top: 16px !important; }
.message-content { margin: 16px 8px !important; }
.icon-button-wrapper button[title="Clear"]::after { content: "Clear"; padding: 0 2px; }
#cmp_chatbot .placeholder img { height: 32px; }
#component-9 { border: solid #808080 1px !important; }
"""

def fn_chatbot(message, history):
    dvcsa_res = DVC_SearchAssist(message)
    bot_suggestions = "## Một số thủ tục liên quan:\n" + "\n".join([f"* `{e['code']}` [{e['name']}]({e['link']})" for e in dvcsa_res['suggestions']])
    bot_response = [
        dvcsa_res['content'],
        bot_suggestions,
    ]
    bot_response = [str(e) for e in bot_response]

    # Just streaming, if no, just simply return bot_response
    bot_response_stream = []
    for iii, eee in enumerate(bot_response):
        bot_response_stream.append("")
        eee = re.split(r'(\s)', eee)
        for i in range(len(eee)):
            time.sleep(0.001)
            bot_response_stream[iii] += eee[i]
            yield(bot_response_stream)

demo = gr.ChatInterface(
    title="Chatbot hỗ trợ tìm kiếm thủ tục",
    fn=fn_chatbot, 
    type="messages", theme=theme, head=head, css=css, analytics_enabled=False,
    chatbot=gr.Chatbot(elem_id="cmp_chatbot", type="messages", group_consecutive_messages=False, container=False,
        placeholder="![image](https://raw.githubusercontent.com/baobuiquang/DVC_SearchAssistant_V2/refs/heads/main/static/logo.png)\n## Xin chào!\nMình là chatbot hỗ trợ tìm kiếm thủ tục dịch vụ công.",
        avatar_images=(None, "https://raw.githubusercontent.com/baobuiquang/DVC_SearchAssistant_V2/refs/heads/main/static/logo.png")),
    textbox=gr.Textbox(elem_id="cmp_textbox", submit_btn=True, stop_btn=True, placeholder="Nhập câu hỏi ở đây"),
    examples = [
        "Vợ tôi sắp sinh con tôi cần làm gì?",
        "Giấy tờ cần thiết để mình khởi nghiệp.",
        "Tôi muốn tố cáo hàng xóm trồng cần sa.",
        "Tôi muốn thành lập công ty tnhh 1 thành viên",
        "Tôi muốn thành lập công ty tnhh 2 thành viên",
        "Tôi muốn thành lập công ty tnhh 9 thành viên",
        "Đấu thầu đất xây dựng",
        "Làm sao để cưới chồng?",
        "Đất đai",
        "Thủ tục chuyển trường cấp 3",
        "Cấp lý lịch tư pháp",
        "Cháu muốn phúc khảo bài thi thpt",
    ],
)
app = gr.mount_gradio_app(app, demo, path="/demo")

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

if __name__ == "__main__":
    # uvicorn.run(app, host = "localhost", port = 5002)
    # uvicorn.run(app, host = "localhost", port = 5002, log_level="critical", log_config=None)
    uvicorn.run(app, host = "0.0.0.0", port = 5002, log_level="critical", log_config=None)