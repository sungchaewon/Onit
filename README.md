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

사용자 입력은 다음 3가지로 구성됩니다.

1. 레퍼런스 케이크 사진 최대 4장
2. 각 사진에 대한 태그 버튼
   - 가게 스타일 참고
   - 가장 비슷한 결과물
   - 색감 참고
   - 장식 참고
3. 자연어 주문 설명문

## Folder Structure

```text
.
├── data/
│   ├── images/          # 레퍼런스 케이크 이미지
│   ├── labels/          # 라벨 스키마와 이미지 metadata
│   ├── demo_orders/     # 데모 주문 JSON
│   └── generated/       # ComfyUI 생성 결과 이미지
├── comfyui_workflows/   # ComfyUI workflow JSON
├── scripts/             # Python 파이프라인 스크립트
├── frontend/            # React 시연용 UI
├── docs/                # 프로젝트 문서
└── README.md
```

## Pipeline

1. 사용자가 레퍼런스 이미지, 이미지별 태그, 자연어 주문 설명문을 입력합니다.
2. Gemini가 이미지와 태그 metadata, 설명문을 함께 해석합니다.
3. Gemini가 주문에 필요한 요소를 구조화된 주문 초안 JSON으로 정리합니다.
4. Prompt Builder가 주문 초안 JSON을 ComfyUI용 positive/negative prompt로 변환합니다.
5. ComfyUI와 IPAdapter가 대표 레퍼런스 이미지를 참고해 케이크 디자인 mockup 이미지를 생성합니다.
6. React UI가 입력 흐름, 주문 초안 JSON, 레퍼런스 분석, 생성 이미지를 시연합니다.

자세한 설명은 [docs/pipeline.md](docs/pipeline.md)를 참고합니다.

## Current Scope

현재 단계에서는 API 연동보다 데이터 구조와 시연 흐름을 먼저 정리합니다.

포함된 작업:

- 파이프라인 문서 작성
- 레퍼런스 이미지 라벨링 문서 작성
- reference image metadata schema 작성
- 하늘색 하트형 장미 파이핑 케이크 데모 주문 JSON 작성

아직 구현하지 않는 작업:

- 실시간 Gemini API 호출
- 실시간 ComfyUI API 호출
- 이미지 업로드 서버
- 실제 주문, 결제, 제작 연동

## Key Files

- [docs/pipeline.md](docs/pipeline.md): 전체 파이프라인 설명
- [docs/data_labeling.md](docs/data_labeling.md): 레퍼런스 이미지 태그와 metadata 설명
- [data/labels/label_schema.json](data/labels/label_schema.json): reference image metadata schema
- [data/demo_orders/demo_001.json](data/demo_orders/demo_001.json): 데모 주문 데이터

## Next Steps

1. `data/images/`에 레퍼런스 케이크 이미지 5-10장을 추가합니다.
2. `data/labels/label_schema.json`을 기준으로 이미지별 metadata 예시를 작성합니다.
3. `data/demo_orders/`에 스타일이 다른 데모 주문 JSON을 추가합니다.
4. `scripts/`에 주문 초안 JSON을 prompt로 바꾸는 Prompt Builder를 구현합니다.
5. `comfyui_workflows/`에 IPAdapter 기반 workflow JSON을 저장합니다.
6. `frontend/`에서 데모 주문 JSON과 생성 이미지를 보여주는 React UI를 구현합니다.

## Tech Stack

- Gemini
- ComfyUI
- IPAdapter
- Python
- React
