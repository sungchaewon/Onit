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
        "shop_selection": {
            "shop_id": "nuni_cake",
            "shop_name": "누니케이크",
        },
        "user_input": {
            "lettering_text": "HAPPY BIRTHDAY",
            "size_and_flavor": "1호 / 바닐라시트 + 우유생크림",
            "additional_requests": (
                "레퍼런스 이미지의 원형 케이크 구도와 중앙 분홍색 곡선 배너를 유지하고, "
                "문구는 HAPPY BIRTHDAY로 변경. "
                "케이크 바탕은 하늘색, 별 장식은 파스텔톤 보라, 핑크, 하늘, 노랑, 연두색으로 배치. "
                "배경은 완전한 흰색으로 정리하고, "
                "풍선, 촛불, 가랜드, 선물상자, 리본, 파티 소품, 테이블, 트레이, 접시, 2단 케이크는 제외."
            ),
        },
        "reference_metadata": [
            {
                "image_id": "ref_001",
                "image_path": "data/images/raw/레터링:큐티2.jpeg",
                "is_store_reference": False,
                "is_closest_reference": True,
                "reference_role": "closest_result",
                "selected_tags": [
                    "closest_result",
                    "shape_reference",
                    "color_reference",
                    "decoration_reference",
                    "composition_reference",
                ],
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
