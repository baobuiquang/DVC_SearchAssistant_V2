from pkg.HYSE.HYSE import Object_HYSE
from pkg.LLM.LLM import Process_LLM
import numpy as np
import json
import csv
import re

def thutuc2content(thutuc_item):
    CHARACTERS_LIMIT = 200
    XEMCHITIET_TEXT = f"... <a href='{thutuc_item['link']}' target='_blank'>(xem chi tiết)</a>"
    bot_response = f"""\
<h2>Thủ tục: {thutuc_item['name'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['name']) > CHARACTERS_LIMIT else ''}</h2>\
<h3>Trình tự thực hiện:</h3>\
<p>{thutuc_item['Trình tự thực hiện'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Trình tự thực hiện']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Cách thức thực hiện:</h3>\
<p>{thutuc_item['Cách thức thực hiện'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Cách thức thực hiện']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Thành phần hồ sơ:</h3>\
<p>{thutuc_item['Thành phần hồ sơ'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Thành phần hồ sơ']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Thời gian giải quyết:</h3>\
<p>{thutuc_item['Thời gian giải quyết'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Thời gian giải quyết']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Đối tượng thực hiện:</h3>\
<p>{thutuc_item['Đối tượng thực hiện'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Đối tượng thực hiện']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Cơ quan thực hiện:</h3>\
<p>{thutuc_item['Cơ quan thực hiện'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Cơ quan thực hiện']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Kết quả:</h3>\
<p>{thutuc_item['Kết quả'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Kết quả']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Phí, lệ phí:</h3>\
<p>{thutuc_item['Phí, lệ phí'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Phí, lệ phí']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Tên mẫu đơn, tờ khai:</h3>\
<p>{thutuc_item['Tên mẫu đơn, tờ khai'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Tên mẫu đơn, tờ khai']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Yêu cầu, điều kiện:</h3>\
<p>{thutuc_item['Yêu cầu, điều kiện'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Yêu cầu, điều kiện']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Căn cứ pháp lý:</h3>\
<p>{thutuc_item['Căn cứ pháp lý'][:CHARACTERS_LIMIT]}{XEMCHITIET_TEXT if len(thutuc_item['Căn cứ pháp lý']) > CHARACTERS_LIMIT else ''}</p>\
<h3>Xem đầy đủ văn bản thủ tục tại:</h3>\
<a href='{thutuc_item['link']}' target='_blank'>{thutuc_item['link']}</a>"""
    return bot_response

def thutuc2context(thutuc_item):
    return f"""\
### Thủ tục: {thutuc_item['name']}
Trình tự thực hiện:
{thutuc_item['Trình tự thực hiện']}
Cách thức thực hiện:
{thutuc_item['Cách thức thực hiện']}
Thành phần hồ sơ:
{thutuc_item['Thành phần hồ sơ']}
Thời gian giải quyết:
{thutuc_item['Thời gian giải quyết']}
Đối tượng thực hiện:
{thutuc_item['Đối tượng thực hiện']}
Cơ quan thực hiện:
{thutuc_item['Cơ quan thực hiện']}
Kết quả:
{thutuc_item['Kết quả']}
Phí, lệ phí:
{thutuc_item['Phí, lệ phí']}
Tên mẫu đơn, tờ khai:
{thutuc_item['Tên mẫu đơn, tờ khai']}
Yêu cầu, điều kiện:
{thutuc_item['Yêu cầu, điều kiện']}
Căn cứ pháp lý:
{thutuc_item['Căn cứ pháp lý']}
"""

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

# -----
# Read cache_2
with open("url/cache_2", mode="r", newline="", encoding="utf-8") as f:
    thutucs = [e for e in csv.DictReader(f)]
    thutuc_keys = list(thutucs[0].keys())
    thutuc_names = [e['name'] for e in thutucs]

# -----
# Create/update HYSE db if needed
docs = [f"{e['name']}" for e in thutucs]
hyse_engine = Object_HYSE()
for i in range(0, len(docs), 50):
    print(i, end=" ")
    hyse_engine.update(docs[:i])
    # time.sleep(3)
hyse_engine.update(docs)

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

def DVC_SearchAssist(input_text):
    # ================================================== HYSE Search
    # -----
    queries = [input_text]
    hyse_search_result = hyse_engine.search(queries)

    # -----
    res_search_all_idx = []
    for possible_thutuc in hyse_search_result[0]:
        for iidx, original_thutuc_name in enumerate(thutuc_names):
            if original_thutuc_name in possible_thutuc["content"]:
                res_search_all_idx.append(iidx)
                break

    # ================================================== LLM Prompt
    p_danhsachthutuc = [{"Mã chuẩn": thutucs[idx]["code"], "Tên thủ tục": thutucs[idx]["name"]} for idx in res_search_all_idx]
    p_json_schema_1 = """\
    {
        "type": "object",
        "properties": {
            "Mã chuẩn": {"type": "string", "description": "Mã chuẩn của thủ tục liên quan nhất"},
            "Tên thủ tục": {"type": "string", "description": "Tên của thủ tục liên quan nhất"}
        }
    }"""
    prompt_1 = f"""\
    Bạn sẽ được cung cấp: (1) Câu hỏi của người dùng, (2) Danh sách thủ tục hiện có, và (3) Schema cấu trúc của kết quả.
    Nhiệm vụ của bạn là: (4) Trích xuất duy nhất 1 thủ tục liên quan nhất đến câu hỏi của người dùng.

    ### (1) Câu hỏi của người dùng:
    "{input_text}"

    ### (2) Danh sách thủ tục hiện có:
    {p_danhsachthutuc}

    ### (3) Schema cấu trúc của kết quả:
    {p_json_schema_1}

    ### (4) Nhiệm vụ:
    Từ câu hỏi của người dùng, tìm ra duy nhất 1 thủ tục liên quan nhất đến câu hỏi của người dùng, tuân thủ schema một cách chính xác.
    Lưu ý quan trọng: Nếu không có thủ tục nào liên quan, trả về "Không có thủ tục liên quan".
    Định dạng kết quả: Không giải thích, không bình luận, không văn bản thừa. Chỉ trả về kết quả JSON hợp lệ. Bắt đầu bằng "{{", kết thúc bằng "}}".
    """

    # ================================================== LLM Processing and Final

    final_obj_for_api = {
        "input": input_text,
        "code": "",
        "name": "",
        "link": "https://dichvucong.lamdong.gov.vn/",
        "content": "Mình có thể giúp được gì cho bạn?",
        "suggestions": [],
        "context_pool": "",
    }
    if input_text.strip() == "":
        return final_obj_for_api

    for _ in range(3):
        llmres1 = Process_LLM(prompt_1)
        regex_match = re.search(r'\{.*\}', llmres1, re.S)
        if regex_match:
            try:
                llm_object_1 = json.loads(regex_match.group())
                llm_object_1_idx_in_thutucs = next((icc for icc, dcc in enumerate(thutucs) if dcc["code"] == llm_object_1["Mã chuẩn"].strip()), -1)
                if llm_object_1_idx_in_thutucs != -1:

                    # ========== The best thutuc by LLM ========== \
                    best_thutuc = thutucs[llm_object_1_idx_in_thutucs]
                    # ========== ---------------------- ========== /

                    # ========== Just thutucs suggestions ========== \
                    MIN_SIM_VS_LLMRES_TO_BE_SUGGESTED = 0.91
                    # -----
                    llm_object_1_id_in_res = -1
                    for iiiccc, eeeccc in enumerate(hyse_search_result[0]):
                        if best_thutuc["name"] == eeeccc["content"]:
                            llm_object_1_id_in_res = iiiccc
                    llm_object_1_id_in_res
                    # -----
                    hyse_res_idxs = []
                    for eee1 in [e['content'] for e in hyse_search_result[0]]:
                        for idxx, eee2 in enumerate(hyse_engine.search_engine_3.docs):
                            if eee1 == eee2:
                                hyse_res_idxs.append(idxx)
                                break
                    hyse_res_embs = np.array([hyse_engine.search_engine_3.embs[e] for e in hyse_res_idxs])
                    similarities = hyse_res_embs @ hyse_res_embs.T
                    hyse_search_result_sim_vs_llmres1 = similarities[llm_object_1_id_in_res]
                    # -----
                    hyse_search_result_filtered = [hyse_search_result[0][ell]["content"] for ell in [ill2 for ill2 in sorted(range(len(hyse_search_result_sim_vs_llmres1)), key=lambda ill: hyse_search_result_sim_vs_llmres1[ill], reverse=True) if hyse_search_result_sim_vs_llmres1[ill2] >= MIN_SIM_VS_LLMRES_TO_BE_SUGGESTED]]
                    # -----
                    suggest_thutucs = []
                    context_pool_from_suggestions = []
                    for eee3 in hyse_search_result_filtered:
                        eee3_idx_in_thutucs = next((icc for icc, dcc in enumerate(thutucs) if dcc["name"] == eee3), -1)
                        suggest_thutucs.append({
                            "code": thutucs[eee3_idx_in_thutucs]["code"],
                            "name": thutucs[eee3_idx_in_thutucs]["name"],
                            "link": thutucs[eee3_idx_in_thutucs]["link"],
                        })
                        context_pool_from_suggestions.append(thutuc2context(thutucs[eee3_idx_in_thutucs]))
                    # ========== ------------------------- ========== /

                    context_pool_from_bestthutuc  = thutuc2context(best_thutuc)
                    context_pool_from_suggestions = "\n\n".join(context_pool_from_suggestions)

                    # ========== Return ========== \
                    final_obj_for_api["code"] = best_thutuc["code"]
                    final_obj_for_api["name"] = best_thutuc["name"]
                    final_obj_for_api["link"] = best_thutuc["link"]
                    final_obj_for_api["content"] = thutuc2content(best_thutuc)
                    final_obj_for_api["suggestions"] = suggest_thutucs
                    # final_obj_for_api["context_pool"] = context_pool_from_bestthutuc
                    # ========== ------ ========== /

                    break
            except:
                pass

    return final_obj_for_api

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================

# questions_for_test = [
#     "Vợ tôi sắp sinh con tôi cần làm gì?",
#     "Giấy tờ cần thiết để mình khởi nghiệp.",
#     "Tôi muốn tố cáo hàng xóm trồng cần sa.",
#     "Làm sao để cưới vợ?",
#     "Tôi muốn thành lập công ty tnhh 2 thành viên",
#     "Tôi muốn thành lập công ty tnhh 3 thành viên",
#     "Mình muốn cưới chồng người nước ngoài",
#     "Cháu muốn phúc khảo bài thi thpt của cháu",
#     "hello bro",
#     "\n",
# ]

# for input_text in questions_for_test:
#     dvcsa_res = DVC_SearchAssist(input_text)
#     print("=" * 100)
#     print("=" * 100)
#     print("=" * 100)
#     for kk in list(dvcsa_res.keys()):
#         if kk == "suggestions":
#             print(f"{kk}:")
#             for e in dvcsa_res[kk]:
#                 print(e)
#         else:
#             print(f"{kk}: {dvcsa_res[kk]}\n")
#     print("-" * 100)

# ====================================================================================================
# ====================================================================================================
# ====================================================================================================