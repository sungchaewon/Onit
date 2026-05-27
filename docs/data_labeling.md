# Reference Image Labeling

이 문서는 O-nit에서 사용하는 레퍼런스 케이크 이미지 metadata와 태그 스키마를 설명합니다. 목표는 사용자가 첨부한 이미지가 주문에서 어떤 역할을 하는지 명확히 기록하고, Gemini가 이미지를 해석할 때 불필요한 추측을 줄이는 것입니다.

## 라벨링 목적

주문제작 케이크 요청에서는 사용자가 여러 이미지를 함께 첨부하는 경우가 많습니다. 하지만 각 이미지가 의미하는 바는 다를 수 있습니다.

예를 들어 한 이미지는 색감만 참고하고, 다른 이미지는 장식 배치를 참고할 수 있습니다. 따라서 이미지를 단순히 저장하는 것보다, 이미지별 사용 의도를 metadata로 남기는 것이 중요합니다.

## 기본 태그

사용자는 각 레퍼런스 이미지에 다음 태그 중 하나 이상을 지정할 수 있습니다.

| 태그 key | UI 표시명 | 의미 |
| --- | --- | --- |
| `shop_style_reference` | 가게 스타일 참고 | 특정 케이크 가게나 브랜드의 전체적인 스타일, 마감 방식, 촬영 느낌을 참고합니다. |
| `closest_result` | 가장 비슷한 결과물 | 사용자가 원하는 최종 결과와 가장 가까운 이미지입니다. 대표 레퍼런스로 우선 고려합니다. |
| `color_reference` | 색감 참고 | 케이크의 주요 색상, 배색, 톤을 참고합니다. |
| `decoration_reference` | 장식 참고 | 파이핑, 토퍼, 리본, 과일, 스프링클 등 장식 요소를 참고합니다. |

하나의 이미지에 여러 태그를 붙일 수 있습니다. 예를 들어 어떤 이미지가 최종 결과와 가장 비슷하면서 색감도 참고 대상이라면 `closest_result`와 `color_reference`를 함께 사용할 수 있습니다.

## 이미지 metadata 항목

각 이미지에는 다음 정보를 기록합니다.

- `reference_id`: 이미지별 고유 ID
- `file_path`: 프로젝트 내부 이미지 파일 경로
- `source_type`: 이미지 출처 유형
- `selected_tags`: 사용자가 선택한 태그 목록
- `user_note`: 사용자가 이미지에 대해 남긴 짧은 설명
- `visual_labels`: 이미지에서 관찰되는 시각 요소
- `analysis_hint`: Gemini가 이 이미지를 해석할 때 참고할 지시
- `priority`: 여러 이미지 중 반영 우선순위

## visual_labels 구조

`visual_labels`는 사람이 사전 라벨링하거나 Gemini 분석 결과로 채울 수 있는 시각 정보입니다.

주요 항목은 다음과 같습니다.

- `cake_shape`: 케이크 형태
- `main_colors`: 주요 색상
- `accent_colors`: 보조 색상
- `decorations`: 장식 요소
- `piping_style`: 파이핑 스타일
- `text_style`: 문구 스타일
- `mood_keywords`: 분위기 키워드

이 정보는 처음부터 완벽하게 채울 필요는 없습니다. 프로토타입 단계에서는 사람이 확인 가능한 수준으로 작성하고, 이후 Gemini 분석 결과와 비교하면서 보완합니다.

## priority 사용 기준

`priority`는 이미지가 최종 디자인에 얼마나 강하게 반영되어야 하는지 나타냅니다.

- `high`: 최종 결과와 가장 밀접하게 반영
- `medium`: 특정 요소만 참고
- `low`: 보조 참고 자료

일반적으로 `closest_result` 태그가 있는 이미지는 `high`로 설정합니다. `color_reference` 또는 `decoration_reference`만 있는 이미지는 상황에 따라 `medium`이나 `low`로 설정할 수 있습니다.

## 라벨링 예시

```json
{
  "reference_id": "ref_001",
  "file_path": "data/images/blue_heart_cake_01.jpg",
  "source_type": "user_upload",
  "selected_tags": ["closest_result", "color_reference"],
  "user_note": "전체 모양과 하늘색 색감을 참고하고 싶어요.",
  "visual_labels": {
    "cake_shape": "heart",
    "main_colors": ["sky_blue", "white"],
    "accent_colors": ["pink"],
    "decorations": ["rose_piping", "shell_border"],
    "piping_style": "vintage_rose",
    "text_style": "small_center_text",
    "mood_keywords": ["cute", "soft", "romantic"]
  },
  "analysis_hint": "형태와 색상을 우선 참고하고, 문구는 그대로 복사하지 않는다.",
  "priority": "high"
}
```

## 주의할 점

- 레퍼런스 이미지를 그대로 복제하는 것이 아니라, 주문 의도에 맞는 디자인 가이드로 재구성합니다.
- 이미지 속 문구가 있어도 사용자의 주문 설명문에 적힌 문구를 우선합니다.
- 색상명은 가능하면 영어 key로 저장하고, UI에서는 한국어 표시명을 별도로 매핑합니다.
- 실제 API 구현 전에는 샘플 JSON을 기준으로 입력과 출력 구조를 먼저 고정합니다.
