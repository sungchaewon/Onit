# O-nit Pipeline

O-nit은 주문제작 케이크 주문 과정에서 사용자의 비정형 입력을 구조화된 주문 초안과 디자인 가이드 이미지로 바꾸는 생성형 AI 과목용 프로토타입입니다. 현재 단계에서는 Gemini API와 ComfyUI API를 실시간으로 연결하지 않고, 문서화된 데이터 구조와 샘플 JSON을 기반으로 전체 흐름을 시연하는 것을 목표로 합니다.

## 입력 데이터

사용자는 React 시연 UI에서 다음 정보를 입력한다고 가정합니다.

1. 레퍼런스 케이크 사진 최소 1장, 최대 4장
2. 각 사진에 대한 태그와 역할 metadata
   - 가게 스타일 참고
   - 가장 비슷한 결과물
   - 색감 참고
   - 장식 참고
3. 주문 입력 필드
   - `lettering_text`: 케이크에 넣을 문구
   - `size_and_flavor`: 사이즈와 맛을 한 줄로 입력
   - `additional_requests`: 색감, 분위기, 장식 등 추가 요청
4. 선택한 가게 정보
   - `shop_selection.shop_id`
   - `shop_selection.shop_name`

레퍼런스 이미지는 단순히 이미지 파일만 받는 것이 아니라, 사용자가 어떤 이유로 해당 이미지를 첨부했는지 함께 기록해야 합니다. 같은 이미지라도 "색감 참고"인지 "장식 참고"인지에 따라 Gemini가 해석해야 하는 정보가 달라지기 때문입니다.

초기 입력 JSON 예시는 다음과 같습니다.

```json
{
  "shop_selection": {
    "shop_id": "nuni_cake",
    "shop_name": "누니케이크"
  },
  "user_input": {
    "lettering_text": "HBD!",
    "size_and_flavor": "1호 / 바닐라시트 + 우유생크림",
    "additional_requests": "연두색 키치한 느낌, 딸기 4개, 너무 화려하지 않게"
  },
  "reference_metadata": [
    {
      "image_id": "ref_001",
      "image_path": "data/images/demo_001_reference_01.png",
      "is_store_reference": false,
      "is_closest_reference": true,
      "reference_role": "closest_result",
      "selected_tags": ["closest_result", "color_reference"]
    }
  ]
}
```

## 전체 흐름

### 1. Reference Input Collection

프론트엔드는 사용자가 업로드한 이미지, 이미지별 metadata, 세 가지 주문 입력 필드를 하나의 입력 묶음으로 관리합니다.

예상 입력 예시는 다음과 같습니다.

- 이미지 A: 가장 비슷한 결과물, 색감 참고
- `lettering_text`: "HBD!"
- `size_and_flavor`: "1호 / 바닐라시트 + 우유생크림"
- `additional_requests`: "연두색 키치한 느낌, 딸기 4개, 너무 화려하지 않게"

현재 프로토타입에서는 실제 업로드 기능보다, 준비된 샘플 이미지와 샘플 주문 데이터를 사용해 흐름을 보여주는 것을 우선합니다.

### 2. Gemini Reference Analysis

Gemini는 레퍼런스 이미지와 태그 metadata, 주문 입력 필드를 함께 해석합니다. 이 단계의 목적은 이미지를 그대로 복사하는 것이 아니라, 주문에 필요한 시각적 요소를 분리해 정리하는 것입니다.

분석 대상 예시는 다음과 같습니다.

- 케이크 형태: 원형, 하트형, 사각형 등
- 주요 색상: 하늘색, 흰색, 분홍색 등
- 장식 요소: 장미 파이핑, 리본, 진주 스프링클, 체리 등
- 분위기: 귀여운, 빈티지한, 깔끔한, 화려한 등
- 문구 유무와 내용
- `size_and_flavor`에서 분리한 케이크 사이즈, 시트 맛, 필링 맛
- `additional_requests`에서 나눈 요청 단위
- 참고 이미지별 역할

### 3. Tag-based Reference Attention

사용자가 선택한 이미지 태그는 AI가 어떤 시각 요소를 더 강하게 참고해야 하는지 알려주는 attention signal로 사용합니다. 실제 모델 내부 attention을 직접 제어하는 단계는 아니지만, 프로토타입에서는 태그를 가중치로 변환해 `reference_attention`에 저장합니다.

예시는 다음과 같습니다.

- `closest_result`: 형태와 구도 가중치를 높게 설정
- `color_reference`: 색감 가중치를 높게 설정
- `decoration_reference`: 장식 요소 가중치를 높게 설정
- `shop_style_reference`: 전체 스타일과 무드 가중치를 높게 설정

출력 예시는 다음과 같습니다.

```json
{
  "image_id": "ref_001",
  "selected_tags": ["closest_result", "color_reference"],
  "attention_weights": {
    "shape_weight": 0.63,
    "color_weight": 0.8,
    "decoration_weight": 0.5,
    "style_weight": 0.63,
    "composition_weight": 0.65
  }
}
```

### 4. Shop Context RAG

선택한 케이크 가게의 스타일, 가능 옵션, 제작 제약을 로컬 지식 베이스에서 검색합니다. 현재는 `data/rag/shop_profiles.json`을 사용하는 mock RAG이며, 나중에는 벡터 DB나 검색 API로 확장할 수 있습니다.

RAG context는 주문 초안을 만들 때 다음 정보로 활용됩니다.

- 가게가 자주 만드는 스타일
- 선호 색감과 분위기
- 가능한 케이크 옵션
- 제작상 피해야 할 조건

현재 산출물은 `retrieved_shop_context`에 저장됩니다.

### 5. Structured Order Draft Generation

Gemini 분석 결과는 구조화된 주문 초안 JSON으로 변환됩니다. 이 JSON은 사람이 읽기 쉬운 주문서이면서, 이후 Prompt Builder가 사용할 수 있는 중간 데이터입니다.

주문 초안에는 다음 정보가 포함됩니다.

- `product_type`
- `design_basis`
- `store_template_name`
- `composition_summary`
- `style`
- `main_colors`
- `decoration_elements`
- `has_lettering`
- `lettering_text`
- `lettering_position`
- `lettering_color`
- `cake_shape`
- `cake_size`
- `sheet_flavor`
- `filling_flavor`
- `special_requests`
- `event_context`
- `difficulty`
- 참고 이미지 분석 요약
- 태그 기반 reference attention
- 가게별 RAG context

이 단계의 산출물은 `data/demo_orders/demo_001.json` 같은 데모 파일로 먼저 관리합니다.

### 6. LangGraph-style Workflow

파이프라인은 LangGraph로 확장하기 쉽도록 노드 단위로 나눕니다. 현재는 실제 LangGraph 패키지를 사용하지 않고, `scripts/run_onit_workflow.py`에서 같은 개념을 local mock workflow로 구현합니다.

현재 노드는 다음 순서로 실행됩니다.

1. `parse_user_input`
2. `compute_reference_attention`
3. `retrieve_shop_context`
4. `generate_order_draft`
5. `validate_order_draft`

각 노드의 실행 결과는 `workflow_trace`와 `workflow_graph`에 저장됩니다.

### 7. Prompt Builder

Prompt Builder는 구조화된 주문 초안 JSON을 ComfyUI에서 사용할 positive prompt와 negative prompt로 변환합니다.

예상 변환 방식은 다음과 같습니다.

- positive prompt: 케이크 형태, 색감, 장식, 촬영 구도, 결과물 스타일을 포함
- negative prompt: 손상된 형태, 과도한 텍스트, 흐릿한 이미지, 실제 케이크와 맞지 않는 요소 등을 제외
- IPAdapter reference: 가장 대표성이 높은 레퍼런스 이미지 1장을 선택

현재 단계에서는 Prompt Builder의 실제 Python 구현보다, JSON에 prompt 후보를 포함해 이후 구현 방향을 확인할 수 있게 합니다.

### 8. ComfyUI Image Generation

ComfyUI는 Prompt Builder가 만든 prompt와 대표 레퍼런스 이미지를 사용해 케이크 디자인 mockup 이미지를 생성합니다. IPAdapter는 레퍼런스 이미지의 전체적인 구도나 분위기를 참고하는 역할로 사용합니다.

현재는 실시간 ComfyUI 연동을 구현하지 않습니다. 대신 다음 항목을 준비하는 것을 우선합니다.

- `comfyui_workflows/sdxl_ipadapter_cake_mockup_template.json`에 SDXL + IPAdapter workflow template 저장
- `data/generated/`에 생성 결과 이미지를 저장할 구조
- 데모 주문 JSON에 prompt 후보와 예상 출력 경로 기록

이 workflow template은 바로 API 서버를 호출하는 코드는 아니며, ComfyUI 환경에 설치된 checkpoint, CLIP Vision, IPAdapter custom node 이름에 맞게 수정해서 사용할 수 있는 설계 초안입니다.

### 9. React Demo UI

React UI는 전체 파이프라인을 사용자가 이해할 수 있도록 시연합니다.

UI에서 보여줄 주요 화면은 다음과 같습니다.

- 레퍼런스 이미지 선택 및 태그 지정
- 자연어 주문 설명 입력
- 구조화된 주문 초안 JSON 보기
- 레퍼런스 분석 요약 보기
- 생성된 디자인 mockup 이미지 보기

초기 버전에서는 실제 API 호출 대신 데모 JSON과 샘플 이미지를 불러와 결과를 보여주는 방식으로 구현합니다.

## 현재 구현 범위

현재 단계에서 구현하는 항목은 다음과 같습니다.

- 파이프라인 문서
- 레퍼런스 이미지 라벨링 문서
- 라벨 스키마 JSON
- 데모 주문 JSON
- 태그 기반 reference attention mock
- 로컬 shop profile 기반 RAG mock
- LangGraph-style workflow trace
- SDXL + IPAdapter용 ComfyUI workflow template
- README 정리

현재 단계에서 구현하지 않는 항목은 다음과 같습니다.

- 실시간 Gemini API 호출
- 실시간 ComfyUI API 호출
- 이미지 업로드 서버
- 주문 결제 또는 실제 제작 연동

## 다음 작업 방향

1. 레퍼런스 이미지 5-10장을 `data/images/`에 추가합니다.
2. `data/labels/label_schema.json`에 맞춰 이미지별 metadata를 작성합니다.
3. 데모 주문 JSON을 2-3개 더 추가해 다양한 케이크 스타일을 비교합니다.
4. Prompt Builder Python 스크립트의 입출력 형식을 정합니다.
5. React UI에서 데모 JSON을 읽어 파이프라인 결과를 시각화합니다.
