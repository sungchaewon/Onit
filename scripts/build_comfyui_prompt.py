#!/usr/bin/env python3
"""Build ComfyUI SDXL + IPAdapter prompts from an O-nit order JSON."""

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT_PATH = "data/demo_orders/demo_001.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build ComfyUI prompts from an O-nit demo order JSON."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_PATH,
        help=f"Path to order JSON. Default: {DEFAULT_INPUT_PATH}",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Input JSON root must be an object.")

    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def as_list(value: Any) -> list[Any]:
    """문자열/리스트/빈 값을 prompt 조립에 쓰기 쉬운 리스트로 변환합니다."""
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    if isinstance(value, tuple):
        return [item for item in value if item not in (None, "")]
    if value == "":
        return []
    return [value]


def humanize_keyword(value: Any) -> str:
    """JSON key 스타일 값을 prompt에 자연스럽게 들어갈 영어 구문으로 바꿉니다."""
    return str(value).strip().replace("_", " ")


def join_keywords(values: list[Any]) -> str:
    return ", ".join(humanize_keyword(value) for value in values if str(value).strip())


def dedupe_preserve_order(values: list[str]) -> list[str]:
    """prompt 조각의 중복을 순서 유지 방식으로 제거합니다."""
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        clean_value = value.strip()
        if clean_value and clean_value not in seen:
            seen.add(clean_value)
            deduped.append(clean_value)
    return deduped


def normalize_negative_keyword(value: Any) -> str:
    """주문서의 avoid key를 negative prompt에 맞는 표현으로 정리합니다."""
    keyword = humanize_keyword(value)
    if keyword == "large text":
        return "oversized lettering"
    return keyword


def get_order_sections(data: dict[str, Any]) -> dict[str, Any]:
    """요구된 key와 기존 demo key를 모두 읽어 내부 표준 구조로 정리합니다."""
    user_input = data.get("user_input") or data.get("input_summary") or {}
    reference_metadata = data.get("reference_metadata")

    if reference_metadata is None:
        # demo_001.json의 기존 구조에서는 reference image metadata가 input_summary 안에 있습니다.
        reference_metadata = user_input.get("reference_images", [])

    order_draft = data.get("order_draft") or data.get("structured_order") or {}
    reference_analysis = data.get("reference_analysis") or []

    if not isinstance(order_draft, dict) or not order_draft:
        raise ValueError("order_draft or structured_order is required.")

    return {
        "user_input": user_input,
        "reference_metadata": reference_metadata,
        "order_draft": order_draft,
        "reference_analysis": reference_analysis,
    }


def extract_shape(order_draft: dict[str, Any]) -> str:
    cake = order_draft.get("cake", {})
    shape = cake.get("shape") or order_draft.get("cake_shape") or "custom"
    shape_text = humanize_keyword(shape)

    if shape_text == "custom":
        return "custom cake shape"
    return f"{shape_text} shaped cake"


def extract_colors(order_draft: dict[str, Any]) -> list[str]:
    cake = order_draft.get("cake", {})
    color_palette = order_draft.get("color_palette", {})

    colors: list[Any] = []
    colors.extend(as_list(color_palette.get("main_colors")))
    colors.extend(as_list(cake.get("base_color")))
    colors.extend(as_list(color_palette.get("accent_colors")))

    # 중복 색상은 순서를 유지한 채 제거합니다.
    seen: set[str] = set()
    unique_colors: list[str] = []
    for color in colors:
        color_text = humanize_keyword(color)
        if color_text and color_text not in seen:
            seen.add(color_text)
            unique_colors.append(color_text)

    return unique_colors


def extract_decorations(order_draft: dict[str, Any]) -> list[str]:
    decorations = order_draft.get("decorations", [])
    decoration_phrases: list[str] = []

    for decoration in as_list(decorations):
        if isinstance(decoration, dict):
            parts = [
                decoration.get("color"),
                decoration.get("type"),
                decoration.get("placement"),
            ]
            phrase = " ".join(humanize_keyword(part) for part in parts if part)
            if phrase:
                decoration_phrases.append(phrase)
        else:
            decoration_phrases.append(humanize_keyword(decoration))

    return decoration_phrases


def extract_lettering(order_draft: dict[str, Any]) -> str:
    message = order_draft.get("message", {})

    if not isinstance(message, dict) or not message:
        return "minimal optional lettering"

    text = message.get("text")
    placement = humanize_keyword(message.get("placement", "center"))
    style = humanize_keyword(message.get("style", "simple lettering"))
    color = humanize_keyword(message.get("color", ""))

    if text:
        color_prefix = f"{color} " if color else ""
        return f'{color_prefix}{style}, {placement} lettering reading "{text}"'

    return f"{style}, {placement} lettering"


def extract_mood(order_draft: dict[str, Any], reference_analysis: list[Any]) -> list[str]:
    cake = order_draft.get("cake", {})
    mood_values: list[Any] = []

    mood_values.extend(as_list(cake.get("style_keywords")))

    # reference_analysis의 mood도 보조 정보로만 추가합니다.
    for reference in reference_analysis:
        if not isinstance(reference, dict):
            continue
        visual_labels = reference.get("visual_labels", {})
        if isinstance(visual_labels, dict):
            mood_values.extend(as_list(visual_labels.get("mood_keywords")))

    seen: set[str] = set()
    moods: list[str] = []
    for mood in mood_values:
        mood_text = humanize_keyword(mood)
        if mood_text and mood_text not in seen:
            seen.add(mood_text)
            moods.append(mood_text)

    return moods


def build_positive_prompt(
    order_draft: dict[str, Any], reference_analysis: list[Any]
) -> str:
    """주문 초안에서 SDXL + IPAdapter용 positive prompt를 만듭니다."""
    shape = extract_shape(order_draft)
    colors = extract_colors(order_draft)
    decorations = extract_decorations(order_draft)
    lettering = extract_lettering(order_draft)
    moods = extract_mood(order_draft, reference_analysis)

    prompt_parts = [
        "single isolated custom cake",
        "reference-inspired but not identical",
        shape,
    ]

    if colors:
        prompt_parts.append(f"main colors: {join_keywords(colors)}")

    if decorations:
        prompt_parts.append(f"decoration elements: {join_keywords(decorations)}")

    prompt_parts.extend(
        [
            f"lettering: {lettering}",
            f"style and mood: {join_keywords(moods) if moods else 'clean custom cake style'}",
            "clean 3D cake design mockup for order confirmation",
            "semi-realistic but simplified",
            "show only one cake body",
            "isolated on a completely plain pure white background",
            "no support object, no cake stand, no board, no plate, no tray, no table, no props",
        ]
    )

    return ", ".join(prompt_parts)


def build_negative_prompt(order_draft: dict[str, Any]) -> str:
    """고정 제외 요소와 주문서의 avoid 항목을 합쳐 negative prompt를 만듭니다."""
    negative_parts = [
        "identical copy of the reference image",
        "exact same layout",
        "support object",
        "cake stand, display stand, pedestal, cake board, plate, tray, table",
        "fabric background, props, extra objects",
        "product photography setup",
        "gray studio background",
        "gradient background",
        "blurry, low quality, watermark, logo",
        "oversized lettering",
    ]

    constraints = order_draft.get("design_constraints", {})
    if isinstance(constraints, dict):
        avoid_items = [
            normalize_negative_keyword(item) for item in as_list(constraints.get("avoid"))
        ]
        negative_parts.extend(avoid_items)

    color_palette = order_draft.get("color_palette", {})
    if isinstance(color_palette, dict):
        avoid_colors = join_keywords(as_list(color_palette.get("avoid_colors")))
        if avoid_colors:
            negative_parts.append(f"avoid colors: {avoid_colors}")

    return ", ".join(dedupe_preserve_order(negative_parts))


def update_comfyui_prompt(data: dict[str, Any]) -> dict[str, str]:
    sections = get_order_sections(data)
    order_draft = sections["order_draft"]
    reference_analysis = sections["reference_analysis"]

    positive_prompt = build_positive_prompt(order_draft, reference_analysis)
    negative_prompt = build_negative_prompt(order_draft)

    data["comfyui_prompt"] = {
        "positive": positive_prompt,
        "negative": negative_prompt,
    }

    # 기존 demo JSON에 남아 있는 예전 prompt 필드도 같은 값으로 맞춰 혼선을 줄입니다.
    prompt_builder_output = data.get("prompt_builder_output")
    if isinstance(prompt_builder_output, dict):
        prompt_builder_output["positive_prompt"] = positive_prompt
        prompt_builder_output["negative_prompt"] = negative_prompt

    return data["comfyui_prompt"]


def print_prompts(prompts: dict[str, str]) -> None:
    print("Positive prompt:")
    print(prompts["positive"])
    print()
    print("Negative prompt:")
    print(prompts["negative"])


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)

    data = load_json(input_path)
    prompts = update_comfyui_prompt(data)
    save_json(input_path, data)
    print_prompts(prompts)


if __name__ == "__main__":
    main()
