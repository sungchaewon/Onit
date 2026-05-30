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


def collect_text_values(value: Any) -> list[str]:
    """중첩된 dict/list 안의 문자열을 모두 모아 조건 판단용 텍스트로 만듭니다."""
    if value is None:
        return []
    if isinstance(value, str):
        return [humanize_keyword(value)]
    if isinstance(value, dict):
        texts: list[str] = []
        for child_value in value.values():
            texts.extend(collect_text_values(child_value))
        return texts
    if isinstance(value, list) or isinstance(value, tuple):
        texts = []
        for item in value:
            texts.extend(collect_text_values(item))
        return texts
    return [humanize_keyword(value)]


def contains_any_text(value: Any, keywords: list[str]) -> bool:
    """JSON 구조 어디에든 특정 의미의 문자열이 있는지 느슨하게 확인합니다."""
    joined_text = " ".join(collect_text_values(value)).lower()
    return any(keyword.lower() in joined_text for keyword in keywords)


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


def is_heart_shape(order_draft: dict[str, Any]) -> bool:
    """하트형 케이크일 때 원형으로 생성되는 것을 막기 위한 분기입니다."""
    cake = order_draft.get("cake", {})
    shape = cake.get("shape") or order_draft.get("cake_shape") or ""
    shape_text = humanize_keyword(shape).lower()
    return shape_text in ("heart", "하트")


def has_lettering(order_draft: dict[str, Any]) -> bool:
    """주문 초안에서 실제 문구 생성을 원하는지 판단합니다."""
    explicit_value = order_draft.get("has_lettering")
    if isinstance(explicit_value, bool):
        return explicit_value

    lettering_text = str(order_draft.get("lettering_text", "")).strip()
    if lettering_text:
        return True

    message = order_draft.get("message", {})
    if not isinstance(message, dict):
        return False

    text = str(message.get("text", "")).strip()
    placement = humanize_keyword(message.get("placement", "")).lower()
    style = humanize_keyword(message.get("style", "")).lower()

    return bool(text) and placement != "none" and "optional" not in style


def extract_colors(order_draft: dict[str, Any]) -> list[str]:
    cake = order_draft.get("cake", {})
    color_palette = order_draft.get("color_palette", {})

    colors: list[Any] = []
    colors.extend(as_list(order_draft.get("main_colors")))
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
    decorations = order_draft.get("decorations") or order_draft.get(
        "decoration_elements", []
    )
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
    """레터링이 실제로 필요한 주문일 때만 positive prompt 문구를 만듭니다."""
    if not has_lettering(order_draft):
        return ""

    lettering_text = str(order_draft.get("lettering_text", "")).strip()
    if lettering_text:
        position = humanize_keyword(order_draft.get("lettering_position", "top center"))
        color = humanize_keyword(order_draft.get("lettering_color", ""))
        color_prefix = f"{color} " if color else ""
        return f'{color_prefix}{position} lettering reading "{lettering_text}"'

    message = order_draft.get("message", {})

    if not isinstance(message, dict) or not message:
        return ""

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
    moods = extract_mood(order_draft, reference_analysis)

    prompt_parts = [
        "single isolated custom cake",
        "reference-inspired but not identical",
        shape,
    ]

    if is_heart_shape(order_draft):
        prompt_parts.extend(
            [
                "clearly heart-shaped cake body, not a round cake",
                "sky-blue rose cream piping covering the top surface",
            ]
        )

    if colors:
        prompt_parts.append(f"main colors: {join_keywords(colors)}")

    if decorations:
        prompt_parts.append(f"decoration elements: {join_keywords(decorations)}")

    lettering = extract_lettering(order_draft)
    if lettering:
        prompt_parts.append(f"lettering: {lettering}")

    prompt_parts.extend(
        [
            f"style and mood: {join_keywords(moods) if moods else 'clean custom cake style'}",
            "clean 3D cake design mockup for order confirmation",
            "semi-realistic but simplified",
            "show only one cake body",
            "isolated on a completely plain pure white background",
            "no support object, no cake stand, no board, no plate, no tray, no table, no props",
        ]
    )

    return ", ".join(prompt_parts)


def get_base_negative_terms() -> list[str]:
    """모든 케이크 생성에 항상 적용하는 공통 negative term입니다."""
    return [
        "cake stand",
        "pedestal",
        "support object",
        "cake board",
        "plate",
        "tray",
        "table",
        "fabric background",
        "cloth",
        "props",
        "extra objects",
        "background objects",
        "multiple cakes",
        "hands",
        "people",
        "watermark",
        "logo",
        "blurry",
        "low quality",
        "gray studio background",
        "gradient background",
        "pattern background",
        "product photography setup",
    ]


def has_rose_piping_context(
    order_draft: dict[str, Any], reference_analysis: list[Any]
) -> bool:
    """주문 또는 레퍼런스 분석에 장미 크림 파이핑 맥락이 있는지 확인합니다."""
    decoration_context = {
        "decorations": order_draft.get("decorations"),
        "decoration_elements": order_draft.get("decoration_elements"),
        "reference_analysis": reference_analysis,
    }
    return contains_any_text(
        decoration_context,
        ["rose piping", "rose cream piping", "장미 파이핑", "cream rose"],
    )


def has_reference_copy_risk(
    order_draft: dict[str, Any], reference_metadata: Any
) -> bool:
    """레퍼런스를 참고하되 그대로 복제하지 말아야 하는 상황인지 판단합니다."""
    special_context = {
        "special_requests": order_draft.get("special_requests"),
        "composition_summary": order_draft.get("composition_summary"),
    }

    has_reference_metadata = bool(reference_metadata)
    has_not_identical_request = contains_any_text(
        special_context,
        ["not identical", "복제하지", "참고만"],
    )

    return has_reference_metadata or has_not_identical_request


def get_conditional_negative_terms(
    order_draft: dict[str, Any],
    reference_analysis: list[Any],
    reference_metadata: Any,
) -> list[str]:
    """order_draft와 레퍼런스 정보에 따라 추가할 negative term을 만듭니다."""
    terms: list[str] = []

    if is_heart_shape(order_draft):
        terms.extend(["round cake", "circular cake"])

    if has_rose_piping_context(order_draft, reference_analysis):
        terms.extend(["single large rose", "one big flower"])

    if has_lettering(order_draft):
        terms.extend(["oversized lettering", "unreadable lettering", "misspelled text"])
    else:
        terms.extend(["text", "lettering", "words", "typography"])

    if has_reference_copy_risk(order_draft, reference_metadata):
        terms.extend(
            [
                "identical copy of the reference image",
                "exact same layout",
                "copied design",
            ]
        )

    constraints = order_draft.get("design_constraints", {})
    if isinstance(constraints, dict):
        avoid_items = [
            normalize_negative_keyword(item) for item in as_list(constraints.get("avoid"))
        ]
        terms.extend(avoid_items)

    color_palette = order_draft.get("color_palette", {})
    if isinstance(color_palette, dict):
        avoid_colors = join_keywords(as_list(color_palette.get("avoid_colors")))
        if avoid_colors:
            terms.append(f"avoid colors: {avoid_colors}")

    return terms


def build_negative_prompt(
    order_draft: dict[str, Any],
    reference_analysis: list[Any],
    reference_metadata: Any,
) -> str:
    """base negative 뒤에 조건부 negative를 붙이고 중복 term을 제거합니다."""
    base_negative_terms = get_base_negative_terms()
    conditional_negative_terms = get_conditional_negative_terms(
        order_draft, reference_analysis, reference_metadata
    )

    return ", ".join(
        dedupe_preserve_order(base_negative_terms + conditional_negative_terms)
    )


def update_comfyui_prompt(data: dict[str, Any]) -> dict[str, str]:
    sections = get_order_sections(data)
    order_draft = sections["order_draft"]
    reference_analysis = sections["reference_analysis"]
    reference_metadata = sections["reference_metadata"]

    positive_prompt = build_positive_prompt(order_draft, reference_analysis)
    negative_prompt = build_negative_prompt(
        order_draft, reference_analysis, reference_metadata
    )

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
