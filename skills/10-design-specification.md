# Skill: Moku.com 디자인 & 레이아웃 완전 명세

이 문서는 현재 프로덕션 사이트의 디자인을 1:1로 재현하기 위한 완전한 명세입니다.
Antigravity에서 프론트엔드를 구현할 때 반드시 이 스펙을 따라주세요.
letusibiza.com에서 영감을 받은 미니멀하고 따뜻한 에이전시 스타일입니다.

---

## 1. 색상 팔레트 (CSS Variables)

```css
:root {
  /* ── Core ── */
  --background: #FAFAF9;            /* 오프화이트 배경 */
  --foreground: #2C2825;            /* 소프트 다크 브라운 (메인 텍스트) */
  --primary: #B8935F;               /* 뮤트된 골드 (CTA, 아이콘, 액센트) */
  --primary-hover: #A38568;         /* 골드 hover */
  --accent-text: #8A6420;           /* WCAG AA 접근성 골드 (링크, 활성 텍스트) */
  --logo-gold: #9E7030;             /* 로고 + 히어로 타이틀 강조 색상 */

  /* ── Surfaces ── */
  --card: #FFFFFF;                  /* 카드 배경 */
  --secondary: #F5F3F0;            /* 소프트 베이지 (아이콘 배경, 호버, 부가 영역) */
  --footer-bg: #2C2825;            /* 푸터 배경 (다크 브라운) */
  --footer-text: #E8E5E1;          /* 푸터 텍스트 */

  /* ── Text ── */
  --text-body: #6B6660;            /* 본문 설명 텍스트 */
  --text-secondary: #5C5652;       /* 뮤트 텍스트 (WCAG AA) */

  /* ── Borders ── */
  --border: rgba(44, 40, 37, 0.08);  /* 매우 연한 보더 */
  --border-medium: rgba(44, 40, 37, 0.10); /* 인풋 보더 */
  --border-hover: rgba(44, 40, 37, 0.30);
  --border-gold: rgba(184, 147, 95, 0.20); /* 골드 보더 */
  --border-gold-light: rgba(184, 147, 95, 0.10); /* 푸터 구분선 */

  /* ── Destructive ── */
  --destructive: #C62828;

  /* ── Radius ── */
  --radius: 0.5rem;                /* 기본 */
  /* 실제 사용: rounded-lg (0.5rem), rounded-xl (0.75rem), rounded-2xl (1rem), rounded-full */
}
```

### 색상 사용 규칙
- 배경: 섹션마다 `#FAFAF9`(오프화이트)와 `#FFFFFF`(화이트) 번갈아 사용
- 텍스트: 제목 `#2C2825`, 본문 설명 `#6B6660`, 링크/활성 `#8A6420`
- CTA 버튼: `bg-[#B8935F] hover:bg-[#A38568] text-white`
- 아이콘 배경: `bg-[#F5F3F0]` + `text-[#B8935F]` 아이콘
- 보더: `border-[#2C2825]/6` 또는 `border-[#2C2825]/10`
- 골드 보더: `border-[#B8935F]/20` (뱃지, 아이콘 박스, 소셜 버튼)

---

## 2. 타이포그래피

### 폰트
```css
font-family: 'Noto Sans JP', 'Noto Sans KR', 'M PLUS 1p', sans-serif;
```
Google Fonts에서 preload 방식으로 로드. @import 사용 금지.

### 기본 스타일
```
h1: font-weight 700, line-height 1.4
h2: font-weight 700, line-height 1.5
h3: font-weight 600, line-height 1.5
h4: font-weight 600, line-height 1.6
p:  font-weight 400, line-height 1.8
label: font-weight 500, line-height 1.6
button: font-weight 600, line-height 1.5
```

### 실제 사용 패턴
| 요소 | Tailwind 클래스 |
|------|-----------------|
| 히어로 타이틀 | `text-[64px] font-bold` (또는 `text-5xl md:text-6xl lg:text-7xl`) |
| 히어로 서브타이틀 (골드) | `text-[#9E7030] text-[64px]` |
| 섹션 타이틀 (h2) | `text-4xl md:text-5xl font-bold text-[#2C2825]` |
| 페이지 타이틀 (h1, 서브페이지) | `text-3xl md:text-4xl font-bold text-[#2C2825]` |
| 섹션 설명 | `text-base text-[#6B6660] leading-relaxed` |
| 카드 제목 | `text-lg font-bold text-[#2C2825] leading-tight` |
| 카드 본문 | `text-sm text-[#6B6660] leading-relaxed` |
| 메타 정보 (날짜, 읽기시간) | `text-xs text-[#6B6660]` |
| 폼 라벨 | `text-[15px] font-medium text-[#2C2825]` |
| 네비 링크 | `text-sm font-medium text-[#2C2825]/70 hover:text-[#8A6420]` |
| 네비 링크 (활성) | `text-[#8A6420]` |

---

## 3. 레이아웃 시스템

### 컨테이너
```
container mx-auto px-4 sm:px-6 lg:px-8
```
최대 너비는 Tailwind 기본 `container` (1280px).

### 섹션 패딩
```
홈 섹션: py-28 md:py-36 (매우 넉넉한 여백)
서브페이지: py-16 md:py-20
```

### 섹션 헤딩 패턴 (모든 섹션 공통)
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}
  transition={{ duration: 0.5 }}
  className="text-center mb-20"  // 홈 섹션: mb-20, 서브페이지: mb-12
>
  <h2 className="text-4xl md:text-5xl mb-5 text-[#2C2825] font-bold">
    {t("section.title")}
  </h2>
  <p className="text-base text-[#6B6660] max-w-2xl mx-auto leading-relaxed">
    {t("section.description")}
  </p>
</motion.div>
```

### 배경색 교차 패턴 (홈페이지)
```
Hero:         bg-[#2C2825] (어두운 배경 + 이미지)
VisaProcess:  bg-white
Archive:      bg-[#FAFAF9]
FAQ:          bg-white
InquiryForm:  bg-[#FAFAF9]
Footer:       bg-[#2C2825]
```

---

## 4. 컴포넌트별 디자인 상세

### 4.1 Header
```
- fixed top-0, z-50
- 스크롤 전: bg-transparent
- 스크롤 후 (>20px): bg-white/90 backdrop-blur-md shadow-sm border-b border-[#2C2825]/5
- 높이: h-16 lg:h-20
- 로고: "MOKU" text-xl lg:text-2xl font-bold text-[#9E7030] tracking-tight
- 네비 링크: hidden lg:flex gap-8
  - text-sm font-medium text-[#2C2825]/70 hover:text-[#8A6420]
  - 활성: text-[#8A6420]
- CTA 버튼: bg-[#B8935F] hover:bg-[#A38568] text-white rounded-full px-6 text-sm
- 모바일: 햄버거 → 풀스크린 오버레이 (bg-white/95 backdrop-blur-md)
  - 메뉴 아이템: py-3 px-4 text-lg font-medium rounded-xl
  - 활성: text-[#8A6420] bg-[#B8935F]/5
```

### 4.2 Hero
```
- 풀스크린 이미지 배경: bg-[#2C2825]
- 배경 이미지:
  - object-cover opacity-90
  - filter brightness-95 contrast-105 saturate-[0.85] mix-blend-overlay
  - 한국 궁궐 풍경 등 따뜻한 감성의 Unsplash 이미지
- 다크 오버레이:
  - bg-gradient-to-b from-[#2C2825]/60 via-[#2C2825]/40 to-[#2C2825]/90
  - 텍스트 가독성 확보용
- 중앙 정렬 컨텐츠 (max-w-4xl mx-auto flex flex-col items-center text-center)
  - Badge: bg-white/10 backdrop-blur-md text-[#F5F3F0] border-white/20 rounded-full px-5 py-2
  - 타이틀: text-[64px] font-bold text-white + 두번째 줄 text-[#D1B075] drop-shadow-md
  - 설명: text-lg text-white/90 max-w-2xl leading-[1.65] drop-shadow-md
  - CTA 2개 (가운데 정렬):
    - Primary: bg-[#B8935F] text-white border-[#B8935F] rounded-full px-9 py-6 shadow-lg hover:shadow-xl
    - Secondary: bg-white/10 backdrop-blur-md text-white border-white/30 rounded-full px-9 py-6
  - Trust 인디케이터 중앙 정렬:
    - 컨테이너: flex flex-col items-center gap-3 group cursor-pointer
    - 아이콘 박스: w-14 h-14 bg-white/20 backdrop-blur-md border border-white/30 rounded-2xl shadow-lg transition-all duration-300 group-hover:bg-white/30 group-hover:-translate-y-1
    - 아이콘 색상: text-[#D1B075] drop-shadow-sm
    - 텍스트: text-sm font-bold text-white tracking-wide drop-shadow-md (어두운 배경 제거)
- 하단 페이드아웃 효과:
  - h-48 md:h-72 bg-gradient-to-t from-white to-transparent (다음 섹션으로 자연스러운 전환)
```

### 4.3 VisaProcess
```
- bg-white, py-28 md:py-36
- 스텝 네비: 원형 버튼 (1~6)
  - 활성: w-12 h-12 md:w-14 md:h-14 bg-[#B8935F] text-white shadow-lg
  - 비활성: w-10 h-10 md:w-11 md:h-11 bg-[#FAFAF9] text-[#B8935F]/40 border border-[#B8935F]/20
  - 사이 화살표: ChevronDown (모바일 세로, 데스크톱 가로 rotate-[-90deg])
- 콘텐츠 카드: max-w-lg, min-h-[320px] md:min-h-[400px]
  - border border-[#2C2825]/6 rounded-2xl shadow-sm
  - 아이콘: w-16 h-16 md:w-20 md:h-20 bg-[#F5F3F0] rounded-xl border border-[#B8935F]/20
  - 소요시간 뱃지: bg-[#F5F3F0] text-[#8A6420] border border-[#B8935F]/20 rounded-full
- 하단 팁 박스: bg-[#F5F3F0] rounded-2xl border border-[#2C2825]/6 -mt-8
```

### 4.4 Archive (홈 프리뷰)
```
- bg-[#FAFAF9], py-16 md:py-20
- 카테고리 필터: Badge rounded-full
  - 활성: bg-[#B8935F] text-white border-[#B8935F]
  - 비활성: bg-white border-[#2C2825]/10 hover:bg-[#F5F3F0]
- 그리드: lg:grid-cols-[1.4fr_1fr] gap-6 max-w-4xl mx-auto
  - 피처드(왼): h-72 이미지 + "注目記事" 뱃지 bg-[#B8935F] text-white rounded-full
  - 목록(오): flex gap-3 p-3, 썸네일 w-28 h-24 rounded-lg
- "もっと見る" 버튼: border-[#2C2825]/10 rounded-xl py-6 hover:text-[#8A6420]
```

### 4.5 Archive 리스트 페이지
```
- bg-[#FAFAF9] min-h-screen
- 그리드: md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl
- 카드: rounded-2xl border border-[#2C2825]/6
  - 이미지: h-56 + filter brightness(0.98) contrast(0.95) saturate(0.85)
  - 카테고리 뱃지: absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-full
  - 제목: text-lg font-bold leading-tight line-clamp-2 hover:text-[#8A6420]
  - 설명: text-sm line-clamp-2
  - 메타: Calendar + Clock 아이콘 text-xs
```

### 4.6 FAQ
```
- bg-white, py-28 md:py-36
- max-w-3xl mx-auto
- Accordion: space-y-4
  - AccordionItem: border border-[#2C2825]/6 px-6 rounded-2xl hover:shadow-md
  - Trigger: py-6 font-semibold text-base hover:text-[#8A6420]
  - Content: text-[#6B6660] text-[15px] leading-relaxed pb-6
- 하단 CTA: border border-[#2C2825]/20 rounded-full px-8 py-6
```

### 4.7 InquiryForm
```
- bg-[#FAFAF9], py-28 md:py-36
- 단일 컬럼: max-w-2xl mx-auto
- 연락처 카드: bg-white rounded-2xl border border-[#2C2825]/6 p-8
  - 아이콘 박스: w-12 h-12 bg-[#F5F3F0] rounded-xl
  - 링크 텍스트: text-[#8A6420]
- 폼 카드: bg-white rounded-2xl border border-[#2C2825]/6 p-8
  - 라벨: flex items-center gap-2, 아이콘 + 텍스트 + * (빨간 별)
  - Input: bg-white border-[#2C2825]/10 focus:border-[#B8935F] rounded-lg py-5
  - Select: 동일한 스타일
  - Textarea: resize-none
  - 에러: text-red-500 text-sm mt-1 (role="alert")
  - 제출 버튼: w-full bg-[#B8935F] rounded-full py-6
  - 개인정보 안내: text-xs text-[#6B6660] text-center
```

### 4.8 Community (게시판)
```
- bg-[#FAFAF9] min-h-screen
- 검색/필터 바:
  - 검색: Input + Select (검색 타입) inline
  - 카테고리 필터: Badge rounded-full (question=violet, info=amber, chat=rose)
  - 정렬: Select 드롭다운
- 게시글 목록: bg-white rounded-2xl border border-[#2C2825]/6 divide-y
  - 각 항목: p-6
  - 핀 표시: bg-amber-50 border-l-2 border-amber-400
  - 경험 뱃지: experienced=emerald, inexperienced=sky
  - 카테고리 뱃지: question=violet, info=amber, chat=rose
  - 메타: Eye(조회수) + MessageCircle(댓글) + ThumbsUp(좋아요) + 시간
- 글쓰기 버튼: fixed bottom-6 right-6, bg-[#B8935F] rounded-full w-14 h-14
- 상세 보기: bg-white rounded-2xl shadow-sm border border-[#2C2825]/6 p-8 md:p-10
  - 댓글: border border-[#2C2825]/6 rounded-lg p-4
- 다이얼로그: shadcn Dialog
- 페이지네이션: rounded-full 버튼, 활성 bg-[#B8935F] text-white
```

### 4.9 Footer
```
- bg-[#2C2825] text-[#E8E5E1]
- py-16
- 4컬럼 그리드: md:grid-cols-4 gap-12
  - 로고: text-white text-2xl font-bold
  - 소셜 아이콘: w-10 h-10 rounded-full border border-[#B8935F]/20 hover:bg-[#B8935F]/20
  - 링크: text-sm opacity-80 hover:text-[#B8935F]
  - 섹션 제목: text-white font-semibold text-[15px]
- 하단 바: pt-8 border-t border-[#B8935F]/10
  - 저작권 + 법적 링크 text-sm opacity-70
```

### 4.10 Breadcrumb
```
- text-sm
- 구분자: ChevronRight w-3.5 h-3.5 text-[#2C2825]/30
- 링크: text-[#2C2825]/60 hover:text-[#8A6420]
- 현재 페이지: text-[#6B6660] font-medium
- 첫 항목에 Home 아이콘
```

### 4.11 LanguageSwitcher
```
- 버튼: px-3 py-1.5 rounded-full border border-[#2C2825]/15 hover:bg-[#F5F3F0]
  - Globe 아이콘 w-3.5 h-3.5 text-[#B8935F] + 언어 코드 (JP/KR/EN)
- 드롭다운: bg-white rounded-xl border border-[#2C2825]/10 shadow-lg min-w-[140px]
  - 선택됨: bg-[#F5F3F0] text-[#8A6420] font-medium
  - 미선택: text-[#2C2825] hover:bg-[#FAFAF9]
```

### 4.12 CookieConsent
```
- fixed bottom-0, z-[60]
- bg-white rounded-2xl shadow-xl border border-[#2C2825]/8 p-5 md:p-6
- max-w-3xl mx-auto
- 수락: bg-[#B8935F] hover:bg-[#A38568] text-white rounded-lg px-5 py-2
- 거절: bg-[#F5F3F0] hover:bg-[#E8E5E1] text-[#2C2825] rounded-lg
- X 닫기: hover:bg-[#F5F3F0] text-[#6B6660]
- 애니메이션: y: 100 → 0, opacity: 0 → 1 (0.4s easeOut)
```

### 4.13 SideNav (홈 전용)
```
- fixed bottom-8 left-1/2 -translate-x-1/2, z-40, hidden lg:block
- bg-white/80 backdrop-blur-sm rounded-full py-4 px-6 shadow-sm border border-[#2C2825]/10
- 도트: w-2 h-2 rounded-full bg-[#2C2825]/30
  - hover: bg-[#B8935F] w-3 h-3
- 툴팁: bg-[#2C2825] text-white text-xs px-3 py-1.5 rounded-md
```

### 4.14 SkeletonLoaders
```
- 모든 Skeleton: bg-[#2C2825]/5
- 게시글 리스트: divide-y divide-[#2C2825]/6, p-6
- 기사 카드 그리드: rounded-2xl border border-[#2C2825]/6
- 페이지: min-h-screen bg-[#FAFAF9]
- aria-label 일본어 (로딩 상태 표시)
```

---

## 5. 애니메이션 패턴

### Motion (framer-motion → motion/react)
```tsx
// 페이지 진입 (순차 딜레이)
initial={{ opacity: 0, y: 20 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.5, delay: 0.1 * index }}

// 스크롤 진입
initial={{ opacity: 0, y: 20 }}
whileInView={{ opacity: 1, y: 0 }}
viewport={{ once: true }}
transition={{ duration: 0.5 }}

// 히어로 이미지
initial={{ opacity: 0, scale: 0.95 }}
animate={{ opacity: 1, scale: 1 }}
transition={{ duration: 0.7, delay: 0.3 }}

// CookieConsent (slide up)
initial={{ y: 100, opacity: 0 }}
animate={{ y: 0, opacity: 1 }}
exit={{ y: 100, opacity: 0 }}
transition={{ duration: 0.4, ease: "easeOut" }}
```

### FadeInSection (IntersectionObserver)
```tsx
// threshold: 0.1, rootMargin: "0px 0px -100px 0px"
// 방향: up(기본)/down/left/right
// 이동 거리: 50px
// duration: 0.6s (기본), ease: "easeOut"
```

### CSS Transitions
```
transition-all duration-300     // 기본 (색상, 배경, 보더)
transition-transform duration-700  // 이미지 호버 스케일
transition-opacity              // 툴팁 표시
transition-colors              // 링크, 버튼
```

### 이미지 호버
```
hover:scale-105 transition-transform duration-700 ease-out
```

---

## 6. 이미지 처리 규칙

```css
/* 모든 카드/기사 이미지에 적용 */
filter: brightness(0.98) contrast(0.95) saturate(0.85);

/* 히어로 이미지에 적용 */
filter: brightness(0.95) contrast(1.05) saturate(0.85);
opacity: 0.90;
mix-blend-overlay + 어두운 오버레이 필수
```
- 이 필터들이 따뜻하고 뮤트된 톤을 만들어냄
- Unsplash 이미지 사용 (한국 도시/문화 관련)
- 모든 이미지에 적절한 alt 텍스트 (i18n)
- lazy loading 기본, 히어로만 eager + fetchPriority="high"

---

## 7. 반응형 브레이크포인트

Tailwind 기본 사용:
```
sm:  640px
md:  768px
lg:  1024px
xl:  1280px
```

### 주요 반응형 패턴
```
Hero: 풀스크린 중앙 정렬 (배경화면)
Archive 프리뷰: lg:grid-cols-[1.4fr_1fr] (모바일: 스택)
Archive 리스트: md:grid-cols-2 lg:grid-cols-3
Footer: md:grid-cols-4
Trust 인디케이터: grid-cols-2 md:grid-cols-4
Partners: md:grid-cols-2
Header: lg에서 네비 표시, lg 미만에서 햄버거
SideNav: hidden lg:block
```

---

## 8. 접근성 패턴

```tsx
// 모든 섹션: aria-labelledby + id
<section aria-labelledby="section-heading">
  <h2 id="section-heading">...</h2>
</section>

// 네비: aria-label
<nav aria-label={t("header.mainNav")}>

// 모바일 메뉴: role="dialog" aria-modal="true"

// 폼: aria-invalid, aria-describedby (에러 메시지와 연결)

// 이미지: 모든 img에 alt 텍스트 (i18n)

// 스켈레톤: role="status" aria-label="...を読み込み中"

// sr-only: 스크린 리더 전용 텍스트

// 포커스 링: box-shadow 0 0 0 3px color-mix(in srgb, var(--ring) 50%, transparent)

// Skip navigation: a[href="#main-content"]
```

---

## 9. Admin 대시보드 디자인

```
- bg-[#FAFAF9] min-h-screen
- 로그인: max-w-md mx-auto, 카드 스타일
- 탭: shadcn Tabs, 하단 인디케이터 bg-[#B8935F]
- 통계 카드: grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4
  - bg-white rounded-xl border border-[#2C2825]/6 p-5
  - 아이콘 박스: w-10 h-10 rounded-xl bg-[색상]/10
  - 숫자: text-2xl font-bold
- 문의 목록: bg-white rounded-xl border border-[#2C2825]/6
  - 상태 뱃지: pending=amber, contacted=blue, completed=green
  - 관리자 메모: bg-[#F5F3F0] rounded-lg p-3
- 게시글 관리: 테이블 형태, 핀/삭제 액션
- 기사 관리: 리스트 + 편집 모달
```

---

## 10. 핵심 디자인 원칙 요약

1. **보더**: `border-[#2C2825]/6` (매우 연함, 6~10% opacity)
2. **라운딩**: 카드 `rounded-2xl`, 버튼 `rounded-full`, 인풋 `rounded-lg`
3. **그림자**: `shadow-sm` 기본, 호버 시 `shadow-md` 또는 `shadow-lg`
4. **여백**: 넉넉하게. 섹션 패딩 py-28 md:py-36, 섹션 간 mb-20
5. **애니메이션**: 부드럽고 미니멀. duration 0.3~0.7s, easeOut
6. **색상 제한**: 골드(#B8935F)는 CTA와 아이콘에만. 남용 금지
7. **텍스트 위계**: 3단계만 — #2C2825(제목) > #6B6660(본문) > #8A6420(링크/강조)
8. **카드 패턴**: bg-white border border-[#2C2825]/6 rounded-2xl + p-5~p-8
9. **이미지**: 항상 뮤트 필터 적용 (따뜻한 톤 유지)
10. **폰트**: Noto Sans JP 우선, weight 400/500/600/700만 사용
