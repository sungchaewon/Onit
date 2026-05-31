# O-nit

O-nit은 주문제작 케이크 주문 과정에서 사용자의 비정형 입력을 구조화된 주문 초안과 디자인 가이드 이미지로 변환하는 생성형 AI 과목용 프로토타입입니다.

현재 목표는 실시간 서비스 구현이 아니라, 레퍼런스 이미지와 자연어 설명을 어떻게 해석하고 중간 데이터로 정리할지 설계한 뒤 React 시연 UI에서 전체 흐름을 보여주는 것입니다.

## Project Goal

사용자는 주문하고 싶은 케이크의 레퍼런스 사진과 간단한 설명을 입력합니다. O-nit은 이 입력을 바탕으로 다음 결과를 만드는 것을 목표로 합니다.

- 구조화된 주문 초안 JSON
- 레퍼런스 이미지 분석 요약
- ComfyUI에서 사용할 positive/negative prompt
- IPAdapter 기반 케이크 디자인 mockup 이미지
- React UI에서 확인할 수 있는 데모 결과 화면

## Input

사용자 입력은 다음 구조로 구성됩니다.

1. 레퍼런스 케이크 사진 최소 1장, 최대 4장
2. 이미지별 `reference_metadata`
   - `image_id`
   - `image_path`
   - `is_store_reference`
   - `is_closest_reference`
   - `reference_role`
   - `selected_tags`
3. 주문 입력값
   - `lettering_text`
   - `size_and_flavor`
   - `additional_requests`
4. 선택 가게 정보
   - `shop_selection.shop_id`
   - `shop_selection.shop_name`

예시:

```json
{
  "user_input": {
    "lettering_text": "HBD!",
    "size_and_flavor": "1호 / 바닐라시트 + 우유생크림",
    "additional_requests": "연두색 키치한 느낌, 딸기 4개, 너무 화려하지 않게"
  }
}
```

## Folder Structure

```text
.
├── data/
│   ├── images/          # 레퍼런스 케이크 이미지
│   ├── labels/          # 라벨 스키마와 이미지 metadata
│   ├── demo_orders/     # 데모 주문 JSON
│   ├── rag/             # 가게별 스타일/제약 RAG mock 데이터
│   └── generated/       # ComfyUI 생성 결과 이미지
├── comfyui_workflows/   # ComfyUI workflow JSON
├── scripts/             # Python 파이프라인 스크립트
├── frontend/            # React 시연용 UI
├── docs/                # 프로젝트 문서
└── README.md
```

## Pipeline

1. 사용자가 레퍼런스 이미지, 이미지별 metadata, 주문 입력값을 입력합니다.
2. 태그 기반 attention mock이 레퍼런스별 참고 가중치를 계산합니다.
3. 로컬 RAG mock이 선택 가게의 스타일, 가능 옵션, 제작 제약을 검색합니다.
4. Gemini 또는 fallback mock이 이미지 metadata, 입력값, RAG context를 함께 해석합니다.
5. 주문에 필요한 요소를 `order_draft` JSON으로 정리합니다.
6. LangGraph-style workflow trace가 각 처리 단계를 노드 단위로 기록합니다.
7. Prompt Builder가 주문 초안 JSON을 ComfyUI용 positive/negative prompt로 변환합니다.
8. ComfyUI와 IPAdapter가 대표 레퍼런스 이미지를 참고해 케이크 디자인 mockup 이미지를 생성합니다.
9. React UI가 입력 흐름, 주문 초안 JSON, 레퍼런스 분석, 생성 이미지를 시연합니다.

자세한 설명은 [docs/pipeline.md](docs/pipeline.md)를 참고합니다.

## Current Scope

현재 단계에서는 API 연동보다 데이터 구조와 시연 흐름을 먼저 정리합니다.

포함된 작업:

- 파이프라인 문서 작성
- 레퍼런스 이미지 라벨링 문서 작성
- reference image metadata schema 작성
- 하늘색 하트형 장미 파이핑 케이크 데모 주문 JSON 작성
- 태그 기반 reference attention mock 구현
- 가게별 RAG profile mock 구현
- LangGraph로 확장 가능한 workflow script 구현

아직 구현하지 않는 작업:

- 실시간 Gemini API 호출
- 실시간 ComfyUI API 호출
- 이미지 업로드 서버
- 실제 주문, 결제, 제작 연동

## Key Files

- [docs/pipeline.md](docs/pipeline.md): 전체 파이프라인 설명
- [docs/data_labeling.md](docs/data_labeling.md): 레퍼런스 이미지 태그와 metadata 설명
- [data/labels/label_schema.json](data/labels/label_schema.json): reference image metadata schema
- [data/rag/shop_profiles.json](data/rag/shop_profiles.json): 가게별 RAG mock 데이터
- [data/demo_orders/demo_001_input.json](data/demo_orders/demo_001_input.json): 데모 입력 데이터
- [data/demo_orders/demo_001.json](data/demo_orders/demo_001.json): 데모 주문 데이터
- [scripts/run_onit_workflow.py](scripts/run_onit_workflow.py): LangGraph-style local workflow 실행 스크립트

## Local Test Commands

```bash
python scripts/run_onit_workflow.py --input data/demo_orders/demo_001_input.json --output data/demo_orders/demo_001.json
python scripts/build_comfyui_prompt.py --input data/demo_orders/demo_001.json
cd frontend
npm run dev
```

## Next Steps

1. `data/images/`에 레퍼런스 케이크 이미지 5-10장을 추가합니다.
2. `data/labels/label_schema.json`을 기준으로 이미지별 metadata 예시를 작성합니다.
3. `data/demo_orders/`에 스타일이 다른 데모 주문 JSON을 추가합니다.
4. `scripts/`의 입력 생성, 주문 초안 생성, Prompt Builder 흐름을 React UI와 연결합니다.
5. `comfyui_workflows/`에 IPAdapter 기반 workflow JSON을 저장합니다.
6. `frontend/`에서 데모 주문 JSON과 생성 이미지를 보여주는 React UI를 구현합니다.

## Tech Stack

- Gemini
- ComfyUI
- IPAdapter
- Python
- React
