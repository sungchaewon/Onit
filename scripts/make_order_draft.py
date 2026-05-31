#!/usr/bin/env python3
"""Create an O-nit order draft JSON from a demo input JSON.

This script uses a local fallback mock instead of calling Gemini.
"""

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT_PATH = "data/demo_orders/demo_001_input.json"
DEFAULT_OUTPUT_PATH = "data/demo_orders/demo_001.json"
DEFAULT_SHOP_KNOWLEDGE_PATH = "data/rag/shop_profiles.json"

TAG_ATTENTION_PRESETS = {
    "closest_result": {
        "shape_weight": 0.9,
        "color_weight": 0.7,
        "decoration_weight": 0.65,
        "style_weight": 0.75,
        "composition_weight": 0.9,
    },
    "color_reference": {
        "shape_weight": 0.35,
        "color_weight": 0.9,
        "decoration_weight": 0.35,
        "style_weight": 0.5,
        "composition_weight": 0.4,
    },
    "decoration_reference": {
        "shape_weight": 0.35,
        "color_weight": 0.45,
        "decoration_weight": 0.9,
        "style_weight": 0.55,
        "composition_weight": 0.45,
    },
    "shop_style_reference": {
        "shape_weight": 0.45,
        "color_weight": 0.55,
        "decoration_weight": 0.55,
        "style_weight": 0.9,
        "composition_weight": 0.55,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an O-nit order draft JSON.")
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_PATH,
        help=f"Path to input JSON. Default: {DEFAULT_INPUT_PATH}",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to write order draft JSON. Default: {DEFAULT_OUTPUT_PATH}",
    )
    parser.add_argument(
        "--shop-knowledge",
        default=DEFAULT_SHOP_KNOWLEDGE_PATH,
        help=f"Path to local shop RAG profiles. Default: {DEFAULT_SHOP_KNOWLEDGE_PATH}",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Input JSON root must be an object.")

    return data


def load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_json(path)


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def split_size_and_flavor(size_and_flavor: str) -> dict[str, str]:
    """'1호 / 바닐라시트 + 우유생크림' 같은 입력을 주문서 필드로 나눕니다."""
    cake_size = ""
    sheet_flavor = ""
    filling_flavor = ""

    size_part, _, flavor_part = size_and_flavor.partition("/")
    cake_size = size_part.strip()

    if flavor_part:
        sheet_part, _, filling_part = flavor_part.partition("+")
        sheet_flavor = sheet_part.strip()
        filling_flavor = filling_part.strip()

    return {
        "cake_size": cake_size,
        "sheet_flavor": sheet_flavor,
        "filling_flavor": filling_flavor,
    }


def split_additional_requests(additional_requests: str) -> list[str]:
    """쉼표로 적은 추가 요청을 의미 단위 배열로 나눕니다."""
    return [
        request.strip()
        for request in additional_requests.split(",")
        if request.strip()
    ]


def average_weights(weight_items: list[dict[str, float]]) -> dict[str, float]:
    """여러 태그의 attention weight를 평균 내어 이미지별 가중치로 만듭니다."""
    if not weight_items:
        return {
            "shape_weight": 0.4,
            "color_weight": 0.4,
            "decoration_weight": 0.4,
            "style_weight": 0.4,
            "composition_weight": 0.4,
        }

    keys = weight_items[0].keys()
    return {
        key: round(sum(item[key] for item in weight_items) / len(weight_items), 2)
        for key in keys
    }


def build_reference_attention(
    reference_metadata: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """사용자가 고른 태그를 AI가 참고해야 할 시각 요소별 가중치로 변환합니다."""
    attention_items = []
    for item in reference_metadata:
        selected_tags = item.get("selected_tags", [])
        tag_weights = [
            TAG_ATTENTION_PRESETS[tag]
            for tag in selected_tags
            if tag in TAG_ATTENTION_PRESETS
        ]
        attention_items.append(
            {
                "image_id": item.get("image_id", ""),
                "selected_tags": selected_tags,
                "attention_weights": average_weights(tag_weights),
                "attention_note": "선택 태그를 기반으로 어떤 시각 요소를 더 강하게 참고할지 정한 mock attention입니다.",
            }
        )

    return attention_items


def get_shop_selection(input_data: dict[str, Any]) -> dict[str, str]:
    selection = input_data.get("shop_selection", {})
    if not isinstance(selection, dict):
        return {}

    return {
        "shop_id": str(selection.get("shop_id", "")).strip(),
        "shop_name": str(selection.get("shop_name", "")).strip(),
    }


def retrieve_shop_context(
    input_data: dict[str, Any],
    shop_knowledge: dict[str, Any],
) -> dict[str, Any]:
    """선택한 가게명/id로 로컬 지식 베이스에서 관련 context를 검색합니다."""
    selection = get_shop_selection(input_data)
    shops = shop_knowledge.get("shops", [])
    if not isinstance(shops, list):
        shops = []

    selected_id = selection.get("shop_id", "")
    selected_name = selection.get("shop_name", "")
    matched_shop = None

    for shop in shops:
        if not isinstance(shop, dict):
            continue
        if selected_id and shop.get("shop_id") == selected_id:
            matched_shop = shop
            break
        if selected_name and shop.get("shop_name") == selected_name:
            matched_shop = shop
            break

    if matched_shop is None:
        return {
            "retrieval_query": selected_name or selected_id or "no_shop_selected",
            "matched": False,
            "shop_id": "",
            "shop_name": "",
            "style_keywords": [],
            "preferred_colors": [],
            "available_options": [],
            "constraints": [],
            "retrieval_notes": "선택된 가게와 일치하는 로컬 RAG profile이 없습니다.",
        }

    return {
        "retrieval_query": selected_name or selected_id,
        "matched": True,
        "shop_id": matched_shop.get("shop_id", ""),
        "shop_name": matched_shop.get("shop_name", ""),
        "style_keywords": matched_shop.get("style_keywords", []),
        "preferred_colors": matched_shop.get("preferred_colors", []),
        "available_options": matched_shop.get("available_options", []),
        "constraints": matched_shop.get("constraints", []),
        "retrieval_notes": matched_shop.get("retrieval_notes", ""),
    }


def infer_design_basis(reference_metadata: list[dict[str, Any]]) -> str:
    """레퍼런스 metadata를 바탕으로 디자인 기준을 간단히 추정합니다."""
    if not reference_metadata:
        return "text_only"

    if any(item.get("is_closest_reference") for item in reference_metadata):
        return "closest_reference"

    if any(item.get("is_store_reference") for item in reference_metadata):
        return "store_reference"

    return "reference_images"


def build_reference_analysis(
    reference_metadata: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Gemini 분석 전 단계의 fallback reference summary를 만듭니다."""
    analysis = []
    for item in reference_metadata:
        role = item.get("reference_role", "general_reference")
        analysis.append(
            {
                "image_id": item.get("image_id", ""),
                "reference_role": role,
                "summary": "fallback mock analysis; 실제 Gemini 분석 전 데모용 요약입니다.",
                "selected_tags": item.get("selected_tags", []),
            }
        )
    return analysis


def build_order_draft(input_data: dict[str, Any]) -> dict[str, Any]:
    """초기 입력을 기존 onit_schema의 order_draft 형태로 변환합니다."""
    user_input = input_data.get("user_input", {})
    reference_metadata = input_data.get("reference_metadata", [])

    if not isinstance(user_input, dict):
        raise ValueError("user_input must be an object.")
    if not isinstance(reference_metadata, list):
        raise ValueError("reference_metadata must be a list.")
    if not 1 <= len(reference_metadata) <= 4:
        raise ValueError("reference_metadata must contain 1 to 4 images.")

    size_and_flavor = str(user_input.get("size_and_flavor", "")).strip()
    flavor_fields = split_size_and_flavor(size_and_flavor)
    additional_requests = str(user_input.get("additional_requests", "")).strip()
    special_requests = split_additional_requests(additional_requests)
    lettering_text = str(user_input.get("lettering_text", "")).strip()

    return {
        "product_type": "custom_cake",
        "design_basis": infer_design_basis(reference_metadata),
        "store_template_name": input_data.get("shop_selection", {}).get("shop_name", ""),
        "composition_summary": "레퍼런스 이미지를 참고하되 그대로 복제하지 않고, 태그별 attention과 가게 RAG context를 함께 반영해 주문 초안을 구성합니다.",
        "style": "kitsch",
        "main_colors": ["light_green"],
        "decoration_elements": ["strawberry_4pcs"],
        "has_lettering": bool(lettering_text),
        "lettering_text": lettering_text,
        "lettering_position": "top_center" if lettering_text else "",
        "lettering_color": "",
        "cake_shape": "unknown",
        "cake_size": flavor_fields["cake_size"],
        "sheet_flavor": flavor_fields["sheet_flavor"],
        "filling_flavor": flavor_fields["filling_flavor"],
        "special_requests": special_requests,
        "event_context": "",
        "difficulty": "medium",
    }


def build_workflow_trace() -> list[dict[str, str]]:
    """LangGraph로 확장 가능한 노드 단위 실행 흐름을 데모 JSON에 남깁니다."""
    return [
        {
            "node": "parse_user_input",
            "status": "completed",
            "description": "lettering_text, size_and_flavor, additional_requests를 읽고 기본 주문 입력을 정리합니다.",
        },
        {
            "node": "compute_reference_attention",
            "status": "completed",
            "description": "reference_metadata.selected_tags를 시각 요소별 attention weight로 변환합니다.",
        },
        {
            "node": "retrieve_shop_context",
            "status": "completed",
            "description": "선택 가게명/id로 로컬 RAG profile을 검색합니다.",
        },
        {
            "node": "generate_order_draft",
            "status": "completed",
            "description": "입력, 레퍼런스 분석, RAG context를 order_draft로 정리합니다.",
        },
        {
            "node": "validate_order_draft",
            "status": "completed",
            "description": "필수 필드와 레퍼런스 개수 조건을 확인합니다.",
        },
    ]


def build_output(input_data: dict[str, Any], shop_knowledge: dict[str, Any]) -> dict[str, Any]:
    reference_metadata = input_data.get("reference_metadata", [])
    reference_attention = build_reference_attention(reference_metadata)
    retrieved_shop_context = retrieve_shop_context(input_data, shop_knowledge)

    return {
        "order_id": input_data.get("order_id", "demo_001"),
        "shop_selection": input_data.get("shop_selection", {}),
        "user_input": input_data.get("user_input", {}),
        "reference_metadata": reference_metadata,
        "reference_attention": reference_attention,
        "retrieved_shop_context": retrieved_shop_context,
        "reference_analysis": build_reference_analysis(reference_metadata),
        "order_draft": build_order_draft(input_data),
        "workflow_trace": build_workflow_trace(),
    }


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    shop_knowledge_path = Path(args.shop_knowledge)

    input_data = load_json(input_path)
    shop_knowledge = load_optional_json(shop_knowledge_path)
    output_data = build_output(input_data, shop_knowledge)
    save_json(output_path, output_data)
    print(f"Wrote order draft: {output_path}")


if __name__ == "__main__":
    main()
