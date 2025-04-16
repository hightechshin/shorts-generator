from flask import Blueprint, request, jsonify
from ..controllers.processing_controller import process_parsed_result
from ..assemblers.prompt_assembler import assemble_prompt
# from nlp_parser import parse_input_with_gpt  ← 너가 쓰는 파서 함수로 연결

generate_bp = Blueprint("generate", __name__)

@generate_bp.route("/generate-final-content", methods=["POST"])
def generate_final_content():
    try:
        data = request.get_json()

        user_input = data["input"]
        options = {
            "is_paid": data.get("is_paid", False),
            "naver_client_id": data.get("client_id", ""),
            "naver_client_secret": data.get("client_secret", "")
        }

        # 1. GPT 파싱
        parsed_result = parse_input_with_gpt(user_input)

        # 2. 컨트롤러: 필요한 데이터만 호출
        controller_output = process_parsed_result(parsed_result, options)

        # 3. 텍스트 조립
        final_prompt = assemble_prompt(parsed_result, controller_output)

        return jsonify({
            "prompt": final_prompt,
            "parsed": parsed_result,
            "data": controller_output,
            "status": "ok"
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "fail"
        }), 400
