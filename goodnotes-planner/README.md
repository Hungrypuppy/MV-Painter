# Atelier Planner 2027 — GoodNotes 샘플

![overview](previews/00-overview.png)

가로형 아이패드(4:3, 1366×1024)에 맞춘 하이퍼링크 디지털 플래너 샘플입니다.

- **파일**: `Atelier-Planner-2027.pdf` (21쪽, 링크 395개, 모두 벡터)
- **구성**: 표지 · 목차 · 연간 달력 · 올해의 목표 · 월간 12개월 · 해빗 트래커 · 주간 · 일간 · 줄 노트 · 도트 노트
- **링크**: 오른쪽 월 탭, 상단 메뉴(Index / Year / Goals / Habits / Notes), 목차, 주차·날짜 링크

## GoodNotes에서 쓰는 법
1. PDF를 아이패드로 옮긴 뒤 **공유 → GoodNotes로 열기** (또는 GoodNotes에서 **가져오기**).
2. 링크는 **읽기 모드**(펜 도구를 끈 상태)에서 탭하면 이동합니다.

## 다시 빌드하기
```bash
python3 build.py                 # planner.html 생성
node render.js --previews        # PDF + previews/*.png
python3 fixlinks.py              # 링크를 페이지 직접 이동 방식으로 변환
```
글꼴: Cormorant Garamond, Jost (SIL Open Font License).
