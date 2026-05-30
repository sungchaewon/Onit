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
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Input JSON root must be an object.")

    return data


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
        "store_template_name": "",
        "composition_summary": "레퍼런스 이미지를 참고하되 그대로 복제하지 않고, 입력 요청을 바탕으로 주문 초안을 구성합니다.",
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


def build_output(input_data: dict[str, Any]) -> dict[str, Any]:
    reference_metadata = input_data.get("reference_metadata", [])
    return {
        "order_id": input_data.get("order_id", "demo_001"),
        "user_input": input_data.get("user_input", {}),
        "reference_metadata": reference_metadata,
        "reference_analysis": build_reference_analysis(reference_metadata),
        "order_draft": build_order_draft(input_data),
    }


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    input_data = load_json(input_path)
    output_data = build_output(input_data)
    save_json(output_path, output_data)
    print(f"Wrote order draft: {output_path}")


if __name__ == "__main__":
    main()
