#!/usr/bin/env python3
"""Create a demo O-nit order input JSON."""

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_PATH = "data/demo_orders/demo_001_input.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create demo O-nit order input JSON.")
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to write input JSON. Default: {DEFAULT_OUTPUT_PATH}",
    )
    return parser.parse_args()


def build_demo_input() -> dict[str, Any]:
    """초기 UI에서 받는 실제 입력 형태에 맞춘 demo payload를 만듭니다."""
    return {
        "order_id": "demo_001",
        "user_input": {
            "lettering_text": "HBD!",
            "size_and_flavor": "1호 / 바닐라시트 + 우유생크림",
            "additional_requests": "연두색 키치한 느낌, 딸기 4개, 너무 화려하지 않게",
        },
        "reference_metadata": [
            {
                "image_id": "ref_001",
                "image_path": "data/images/demo_001_reference_01.png",
                "is_store_reference": False,
                "is_closest_reference": True,
                "reference_role": "closest_result",
                "selected_tags": ["closest_result", "color_reference"],
            }
        ],
    }


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    save_json(output_path, build_demo_input())
    print(f"Wrote demo input: {output_path}")


if __name__ == "__main__":
    main()
