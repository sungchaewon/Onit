import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import demo from "./data/demo_001.json";
import generatedCake from "./assets/demo_001.png";
import referenceImage from "./assets/reference_ref_001.jpeg";
import onitLogo from "./assets/onit-logo.svg";
import popularVintageLovely from "./assets/popular_01.jpeg";
import popularFlowerChic from "./assets/popular_02.jpeg";
import popularLetteringCutie from "./assets/popular_03.jpeg";
import popularLetteringKitschTrend from "./assets/popular_04.jpeg";
import popularRollCharacter from "./assets/popular_05.jpeg";
import popularFlowerChicSixth from "./assets/popular_06.jpeg";
import "./styles.css";

const SHOPS = [
  {
    id: 1,
    name: "누니케이크",
    location: "서울 강북구",
    tag: "#하트스노우 #심플 #파스텔",
    rating: "4.9",
    instagram: "https://www.instagram.com/nuni__cake",
  },
  {
    id: 2,
    name: "버터뭉",
    location: "서울 종로구",
    tag: "#캐릭터 #떠먹케 #미니케이크",
    rating: "4.8",
    instagram: "https://www.instagram.com/butter.moong",
  },
  {
    id: 3,
    name: "세히크",
    location: "서울 강북구",
    tag: "#빈티지 #생화케이크 #포토케이크",
    rating: "4.8",
    instagram: "https://www.instagram.com/seheek_cake",
  },
  {
    id: 4,
    name: "호미미케이크",
    location: "대구 중구",
    tag: "#컵케이크 #생화케이크 #돔케이크",
    rating: "4.7",
    instagram: "https://www.instagram.com/homeme.cake",
  },
  {
    id: 5,
    name: "카페선",
    location: "김포 장기동",
    tag: "#과일케이크 #조각케이크 #제철과일",
    rating: "4.7",
    instagram: "https://www.instagram.com/cafe_thesun/",
  },
  {
    id: 6,
    name: "파티세리 송버드",
    location: "서울 강남구",
    tag: "#파인디저트 #시즌디저트 #파블로바",
    rating: "4.5",
    instagram: "https://www.instagram.com/patisserie.songbird/",
  },
];

const POPULAR = [
  { rank: 1, image: popularVintageLovely, label: "빈티지 러블리" },
  { rank: 2, image: popularFlowerChic, label: "생화 시크" },
  { rank: 3, image: popularLetteringCutie, label: "레터링 큐티" },
  { rank: 4, image: popularLetteringKitschTrend, label: "키치 트렌드" },
  { rank: 5, image: popularRollCharacter, label: "롤케익 캐릭터" },
  { rank: 6, image: popularFlowerChicSixth, label: "생화 시크" },
];

const PICKUP_SCHEDULE = [
  {
    date: "05.08 (화)",
    event: "어버이날",
    shop: "파티세리 송버드",
    item: "시즈널 파블로바",
    status: "done",
  },
  {
    date: "06.13 (토)",
    event: "생일",
    shop: "카페선",
    item: "말차바닐라 치즈케이크 1호",
    status: "pending",
  },
];

const SIZES = ["도시락", "미니", "미니롤케이크", "컵케이크", "1호", "2호"];
const REASONS = ["졸업", "생일", "결혼 기념일", "웨딩", "젠더리빌", "입학", "은퇴", "승진", "기타"];
const PHOTO_LABELS = ["색 참고", "모양 참고", "케이크 일러스트", "추가 사진"];
const DAY_LABELS = ["일", "월", "화", "수", "목", "금", "토"];

const tagLabels = {
  closest_result: "가장 비슷한 결과물",
  color_reference: "색감 참고",
  decoration_reference: "장식 참고",
  shop_style_reference: "가게 스타일 참고",
};

function formatValue(value) {
  if (Array.isArray(value)) return value.length ? value.join(", ") : "-";
  if (typeof value === "boolean") return value ? "예" : "아니오";
  return value || "-";
}

function getPickupDaysForMonth(month) {
  return PICKUP_SCHEDULE.reduce((days, pickup) => {
    const match = pickup.date.match(/^(\d{2})\.(\d{2})/);
    if (!match) return days;

    const pickupMonth = Number(match[1]) - 1;
    const pickupDay = Number(match[2]);
    return pickupMonth === month ? [...days, pickupDay] : days;
  }, []);
}

function Calendar({ year, month, onPrev, onNext }) {
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const today = new Date();
  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
  const pickupDays = getPickupDaysForMonth(month);
  const cells = [...Array(firstDay).fill(null), ...Array.from({ length: daysInMonth }, (_, index) => index + 1)];

  return (
    <div className="calendar">
      <div className="calendar-head">
        <button type="button" onClick={onPrev} aria-label="이전 달">
          ‹
        </button>
        <strong>
          {year}년 {month + 1}월
        </strong>
        <button type="button" onClick={onNext} aria-label="다음 달">
          ›
        </button>
      </div>
      <div className="calendar-grid">
        {DAY_LABELS.map((day) => (
          <span className="day-label" key={day}>
            {day}
          </span>
        ))}
        {cells.map((day, index) => {
          const isToday = isCurrentMonth && day === today.getDate();
          const hasPickup = day && pickupDays.includes(day);
          return (
            <span className={`day-cell ${isToday ? "today" : ""}`} key={`${day}-${index}`}>
              {day}
              {hasPickup && <i />}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function Toast({ message }) {
  if (!message) return null;
  return <div className="toast">{message}</div>;
}

function CakeOrderApp() {
  const input = demo.user_input || {};
  const draft = demo.order_draft || {};
  const references = demo.reference_metadata || [];

  const [calDate, setCalDate] = useState({ year: 2026, month: 4 });
  const [shopSearch, setShopSearch] = useState("");
  const [selectedShop, setSelectedShop] = useState(null);
  const [formActive, setFormActive] = useState(false);
  const [photos, setPhotos] = useState(references.map((item, index) => PHOTO_LABELS[index] || `사진 ${index + 1}`));
  const [lettering, setLettering] = useState(Boolean(input.lettering_text));
  const [letteringText, setLetteringText] = useState(input.lettering_text || "");
  const [selectedSize, setSelectedSize] = useState(draft.cake_size || "1호");
  const [reason, setReason] = useState("");
  const [reasonOther, setReasonOther] = useState("");
  const [extraNote, setExtraNote] = useState(input.additional_requests || "");
  const [pickupDatetime, setPickupDatetime] = useState("");
  const [unmanned, setUnmanned] = useState(false);
  const [firstPurchase, setFirstPurchase] = useState(false);
  const [coolerPacking, setCoolerPacking] = useState(false);
  const [qty, setQty] = useState(1);
  const [previewReady, setPreviewReady] = useState(true);
  const [designGenerated, setDesignGenerated] = useState(false);
  const [toast, setToast] = useState("");

  const showToast = (message) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2400);
  };

  const filteredShops = SHOPS.filter(
    (shop) =>
      shop.name.includes(shopSearch) ||
      shop.tag.includes(shopSearch) ||
      shop.location.includes(shopSearch),
  );
  const selectedShopData = SHOPS.find((shop) => shop.id === selectedShop);

  const activateForm = () => {
    if (!selectedShop) {
      showToast("먼저 가게를 선택해주세요");
      return;
    }

    setFormActive(true);
    showToast("주문서가 활성화되었습니다");
  };

  const addPhoto = () => {
    if (photos.length >= 4) {
      showToast("사진은 최대 4장까지 첨부 가능합니다");
      return;
    }
    setPhotos((current) => [...current, PHOTO_LABELS[current.length] || `사진 ${current.length + 1}`]);
  };

  const removePhoto = (targetIndex) => {
    setPhotos((current) => current.filter((_, index) => index !== targetIndex));
  };

  const regenDesign = () => {
    if (!canGenerateDesign) {
      showToast("필수 주문서 항목을 먼저 입력해주세요");
      return;
    }

    setPreviewReady(false);
    setDesignGenerated(false);
    showToast(designGenerated ? "도안을 다시 생성합니다" : "도안을 생성합니다");
    window.setTimeout(() => {
      setPreviewReady(true);
      setDesignGenerated(true);
      showToast("새 도안이 생성되었습니다");
    }, 1100);
  };

  const submitOrder = () => {
    if (!isOrderReady) {
      showToast("예상 도안 생성과 픽업 일시 입력까지 완료해주세요");
      return;
    }
    showToast("주문서가 제출되었습니다");
    window.setTimeout(() => showToast("가게에서 확인 후 연락드립니다"), 2200);
  };

  const summaryParts = [selectedShopData?.name, selectedSize, reason === "기타" ? reasonOther : reason].filter(Boolean);
  const hasReason = reason && (reason !== "기타" || reasonOther.trim());
  const hasLetteringInput = !lettering || letteringText.trim();
  const hasPickupDatetime = Boolean(pickupDatetime);
  const canGenerateDesign = Boolean(
    formActive &&
      selectedShop &&
      photos.length > 0 &&
      selectedSize &&
      hasReason &&
      hasLetteringInput,
  );
  const isOrderReady = Boolean(canGenerateDesign && designGenerated && hasPickupDatetime);
  const orderStatusMessage = !formActive
    ? "가게에서 주문서 작성하기를 눌러주세요"
    : !canGenerateDesign
      ? "필수 항목을 입력하면 도안을 만들 수 있습니다"
    : !designGenerated
      ? "예상 도안을 만든 뒤 픽업 일시를 입력하면 제출할 수 있습니다"
      : !hasPickupDatetime
        ? "픽업 일시를 입력하면 제출할 수 있습니다"
        : summaryParts.length
          ? summaryParts.join(" · ")
          : "필수 항목을 입력하면 주문서 제출이 활성화됩니다";

  return (
    <div className="app-shell">
      <nav className="app-nav">
        <img src={onitLogo} alt="O-nit" />
        <div className="nav-actions">
          <button type="button" onClick={() => showToast("로그인 페이지로 이동합니다")}>
            로그인
          </button>
          <button type="button" className="soft" onClick={() => showToast("회원가입 페이지로 이동합니다")}>
            회원가입
          </button>
          <button type="button" className="icon-btn" onClick={() => showToast("마이페이지")}>
            MY
          </button>
          <button type="button" className="icon-btn has-dot" onClick={() => showToast("알림 3개")}>
            ON
          </button>
        </div>
      </nav>

      <main className="workspace">
        <section className="support-panel">
          <div className="calendar-stack">
            <section className="side-section">
              <h2>픽업 캘린더</h2>
              <Calendar
                year={calDate.year}
                month={calDate.month}
                onPrev={() =>
                  setCalDate((current) => {
                    const date = new Date(current.year, current.month - 1);
                    return { year: date.getFullYear(), month: date.getMonth() };
                  })
                }
                onNext={() =>
                  setCalDate((current) => {
                    const date = new Date(current.year, current.month + 1);
                    return { year: date.getFullYear(), month: date.getMonth() };
                  })
                }
              />
            </section>

            <section className="side-section">
              <h2>픽업 일정</h2>
              {PICKUP_SCHEDULE.map((pickup) => (
                <div className="pickup-item" key={`${pickup.date}-${pickup.shop}`}>
                  <span>
                    {pickup.date} · {pickup.event}
                  </span>
                  <strong>{pickup.shop}</strong>
                  <p>{pickup.item}</p>
                  <em className={pickup.status}>{pickup.status === "pending" ? "픽업 예정" : "픽업 완료"}</em>
                </div>
              ))}
            </section>
          </div>

          <section className="side-section shop-section">
            <h2>케이크 가게 검색</h2>
            <input
              value={shopSearch}
              onChange={(event) => setShopSearch(event.target.value)}
              placeholder="가게명 또는 태그 검색"
            />
            <div className="shop-list">
              {filteredShops.map((shop) => (
                <button
                  type="button"
                  className={`shop-item ${selectedShop === shop.id ? "selected" : ""}`}
                  key={shop.id}
                  onClick={() => setSelectedShop(shop.id)}
                >
                  <strong>{shop.name}</strong>
                  <span>
                    ★ {shop.rating} · {shop.location}
                  </span>
                  <span>{shop.tag}</span>
                  {selectedShop === shop.id && (
                    <div className="shop-actions">
                      {shop.instagram && (
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            window.open(shop.instagram, "_blank", "noopener,noreferrer");
                          }}
                        >
                          인스타 보기
                        </button>
                      )}
                      <button
                        type="button"
                        className="pink"
                        onClick={(event) => {
                          event.stopPropagation();
                          activateForm();
                        }}
                      >
                        주문서 작성하기
                      </button>
                    </div>
                  )}
                </button>
              ))}
            </div>
          </section>

          <section className="side-section popular-section">
            <h2>월간 인기 디자인 TOP6</h2>
            <div className="popular-grid">
              {POPULAR.map((item) => (
                <button type="button" key={item.rank} onClick={() => showToast(`${item.label} 디자인 상세보기`)}>
                  <img src={item.image} alt={item.label} />
                  <span>TOP{item.rank}</span>
                </button>
              ))}
            </div>
          </section>
        </section>

        <section className="main-panel">
          <article className="order-card">
            <header className="order-head">
              <div>
                <h1>주문서 작성</h1>
                <p>{selectedShopData ? `${selectedShopData.name} 주문서` : "가게를 선택하면 주문서가 활성화됩니다"}</p>
              </div>
              <button type="button" className="primary-btn" disabled={!isOrderReady} onClick={submitOrder}>
                주문서 제출하기
              </button>
            </header>

            <div className={`order-form ${formActive ? "" : "disabled"}`}>
              <section>
                <label>
                  레퍼런스 사진 <b>필수</b> <span>최대 4장</span>
                </label>
                {photos.length === 0 ? (
                  <button type="button" className="upload-area" onClick={addPhoto}>
                    <strong>사진 추가</strong>
                    <span>색 참고 / 모양 참고 / 케이크 일러스트 또는 사진 중 택 1</span>
                  </button>
                ) : (
                  <div className="photo-grid">
                    {photos.map((photo, index) => (
                      <div className="photo-slot" key={`${photo}-${index}`}>
                        <img src={referenceImage} alt={photo} />
                        <span>{photo}</span>
                        <button type="button" onClick={() => removePhoto(index)} aria-label={`${photo} 제거`}>
                          ×
                        </button>
                      </div>
                    ))}
                    {photos.length < 4 && (
                      <button type="button" className="photo-add" onClick={addPhoto}>
                        +
                      </button>
                    )}
                  </div>
                )}
                <div className="tag-row">
                  {(references[0]?.selected_tags || []).map((tag) => (
                    <span key={tag}>{tagLabels[tag] || tag}</span>
                  ))}
                </div>
              </section>

              <section>
                <label>
                  레터링 <b>필수</b>
                </label>
                <div className="segmented">
                  <button type="button" className={!lettering ? "active" : ""} onClick={() => setLettering(false)}>
                    레터링 없음
                  </button>
                  <button type="button" className={lettering ? "active" : ""} onClick={() => setLettering(true)}>
                    레터링 있음
                  </button>
                </div>
                {lettering && (
                  <input
                    value={letteringText}
                    onChange={(event) => setLetteringText(event.target.value)}
                    placeholder="레터링 문구를 입력하세요"
                  />
                )}
              </section>

              <section>
                <label>
                  사이즈 <b>필수</b>
                </label>
                <div className="size-row">
                  {SIZES.map((size) => (
                    <button
                      type="button"
                      className={selectedSize === size ? "selected" : ""}
                      key={size}
                      onClick={() => setSelectedSize(size)}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </section>

              <section>
                <label>
                  케이크 주문 목적 <b>필수</b>
                </label>
                <select value={reason} onChange={(event) => setReason(event.target.value)}>
                  <option value="">이유를 선택하세요</option>
                  {REASONS.map((item) => (
                    <option value={item} key={item}>
                      {item === "기타" ? "기타 (직접 입력)" : item}
                    </option>
                  ))}
                </select>
                {reason === "기타" && (
                  <input
                    value={reasonOther}
                    onChange={(event) => setReasonOther(event.target.value)}
                    placeholder="이유를 직접 입력하세요"
                  />
                )}
              </section>

              <section className="additional-section">
                <label>
                  추가 주문 사항 <span>선택</span>
                </label>
                <textarea value={extraNote} onChange={(event) => setExtraNote(event.target.value)} placeholder="추가 요청사항을 입력하세요" />
              </section>
            </div>
          </article>

          <div className="live-grid">
            <article className="preview-card">
              <header>
                <h2>예상 도안</h2>
                <button type="button" disabled={!canGenerateDesign} onClick={regenDesign}>
                  {designGenerated ? "다시 만들기" : "도안 만들기"}
                </button>
              </header>
              <div className={`preview-frame ${previewReady ? "ready" : ""}`}>
                {previewReady ? <img src={generatedCake} alt="생성된 케이크 도안" /> : <strong>AI 도안 생성 중...</strong>}
              </div>
            </article>

            <article className="pickup-card">
              <h2>픽업 정보</h2>
              <label>
                픽업 일시
                <input type="datetime-local" value={pickupDatetime} onChange={(event) => setPickupDatetime(event.target.value)} />
              </label>
              <label className="check-line">
                <input
                  type="checkbox"
                  checked={unmanned}
                  onChange={(event) => {
                    setUnmanned(event.target.checked);
                    showToast(event.target.checked ? "무인 픽업 설정됨" : "유인 픽업으로 변경");
                  }}
                />
                무인 픽업
              </label>
              <label className="check-line">
                <input type="checkbox" checked={firstPurchase} onChange={(event) => setFirstPurchase(event.target.checked)} />초 구매 여부
              </label>
              <label className="check-line">
                <input type="checkbox" checked={coolerPacking} onChange={(event) => setCoolerPacking(event.target.checked)} />
                보냉 포장 필요
              </label>
              {firstPurchase && (
                <div className="qty-row">
                  <button type="button" onClick={() => setQty((current) => Math.max(1, current - 1))}>
                    -
                  </button>
                  <strong>{qty}</strong>
                  <button type="button" onClick={() => setQty((current) => current + 1)}>
                    +
                  </button>
                  <span>개</span>
                </div>
              )}
              <p className="order-hint">{orderStatusMessage}</p>
            </article>
          </div>
        </section>
      </main>

      <Toast message={toast} />
    </div>
  );
}

createRoot(document.getElementById("root")).render(<CakeOrderApp />);
