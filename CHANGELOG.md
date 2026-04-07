# W-BOSS 기상 작전 지원 시스템 업데이트 내역

---

## v2.3 (최신 업데이트) — 2026-03-30  보안 감사 · 계급 · 군번 유효성 강화

### 개요

이번 업데이트는 **보안 감사(Audit Log) 체계 구축**과 **계급 관리 기능 추가**, **군번 형식 유효성 강화**를 핵심으로 합니다. 단순히 "수정했다"는 기록이 아니라 **변경 전/후 데이터(Before & After)**, **IP 주소**, **User-Agent** 까지 남겨 사고 발생 시 복구 및 원인 추적이 가능하도록 설계하였습니다.

---

### 신규 파일

| 파일 | 설명 |
|---|---|
| `functions/audit_logger.py` | 감사 로그 기록·조회 전담 모듈 (신규) |

---

### DB 변경 (`DB_create.sql`)

| 항목 | 내용 |
|---|---|
| `USERS.military_rank` | `VARCHAR(50)` 계급 컬럼 추가 (장교·부사관·병·기타) |
| `AUDIT_LOG` 테이블 | 신규 생성 — `user_id`, `service_number`, `action_type`, `page`, `before_data(JSON)`, `after_data(JSON)`, `description`, `ip_address`, `device_info`, `created_at` |
| 기본 계정 INSERT | admin(`99-99999`), 테스트 장교(`25-12345`), 부사관(`22-123456`), 병(`26-12345678`) 샘플 계정 추가 (비밀번호는 평문 비교로 유지) |
| 마이그레이션 주석 | 기존 DB에 `military_rank` 컬럼 추가 시 사용할 `ALTER TABLE` 구문 주석으로 포함 |

---

### `functions/audit_logger.py` (신규)

감사 로그의 모든 기록·조회를 담당하는 전담 모듈입니다.

**기록되는 행위 유형 (`action_type`)**

| 값 | 트리거 시점 |
|---|---|
| `LOGIN` | 로그인 성공 |
| `LOGOUT` | 로그아웃 |
| `REGISTER` | 회원가입 완료 |
| `PASSWORD_CHANGE` | 비밀번호 변경 성공 |
| `PROFILE_UPDATE` | 계급 등 프로필 수정 — **Before/After JSON 기록** |
| `ACCOUNT_DELETE` | 회원 탈퇴(Soft Delete) |
| `PAGE_ACCESS` | 주요 페이지 접근 (홈, 마이페이지) |
| `DATA_EXPORT` | 데이터 다운로드·내보내기 (향후 연동 준비) |

---

### `functions/auth_functions.py`

| 변경 항목 | 내용 |
|---|---|
| 군번 정규식 | `^\d{2}-\d{7,8}$` → `^\d{2}-(?:\d{5}|\d{6}|\d{8})$` |
| `validate_service_number()` | 반환값 `bool` → `(bool, str)` 튜플로 변경 (오류 메시지 포함) |
| `get_role_by_sn()` | 군번 뒷자리 길이로 role 자동 추정 (5자리→officer, 6자리→nco, 8자리→soldier) 신규 추가 |
| `register_user()` | `role` 파라미터 제거 → `get_role_by_sn()` 자동 추정으로 변경 |
| `set_authenticated()` | 로그인 성공 시 `audit_login()` 호출 추가 |
| `logout()` | 로그아웃 시 `audit_logout()` 호출 추가 (세션 소멸 전 기록) |
| `delete_user()` | 탈퇴 처리 후 `audit_account_delete()` 호출 추가 |

**군번 형식 안내**

| 구분 | 형식 | 예시 |
|---|---|---|
| 장교 | `YY-NNNNN` (5자리) | `25-12345` |
| 부사관 | `YY-NNNNNN` (6자리) | `22-123456` |
| 병 | `YY-NNNNNNNN` (8자리) | `26-12345678` |

---

### `pages/my_page.py` (전면 재작성)

| 탭 | 내용 | 접근 권한 |
|---|---|---|
| ◈ 프로필 | 계정 정보 조회 + **계급 수정** (군번은 읽기 전용) | 전체 |
| ◈ 비밀번호 변경 | 현재 비밀번호 확인 후 변경 + 감사 로그 기록 | 전체 |
| ◈ 내 접속 기록 | 본인 ACCESS_LOG 최근 20건 | 전체 |
| ◈ 내 감사 로그 | 본인 AUDIT_LOG 최근 50건 | 전체 |
| ◈ 전체 접속 로그 [ADMIN] | 전체 사용자 ACCESS_LOG 최근 100건 | **admin 전용** |
| ◈ 전체 감사 로그 [ADMIN] | 전체 사용자 AUDIT_LOG 최근 200건 | **admin 전용** |

- 계급 수정 시 Before/After JSON이 `AUDIT_LOG`에 자동 기록됨
- 페이지 접근 자체도 세션당 1회 `PAGE_ACCESS` 로그로 기록됨

---

### `pages/register_page.py`

- 군번 입력 필드 placeholder를 `장교 25-12345 / 부사관 22-123456 / 병 26-12345678` 형식으로 변경
- 입력 필드 하단에 형식 안내 텍스트 추가
- 회원가입 성공 시 `audit_register()` 호출 추가

---

### `functions/render_html.py` + `style/topbar.css`

- `render_topbar()` 에 `authenticated`, `username` 파라미터 추가
- **로그인 상태**: `{username}` 표시 + `마이페이지` + `로그아웃(빨간색)` 버튼
- **비로그인 상태**: `로그인` + `회원가입(초록색)` 버튼 (기존 유지)
- CSS에 `.auth-user`, `.auth-btn.logout` 스타일 추가

---

### `functions/state_functions.py`

- `get_dashboard_context()` 반환 dict에 `authenticated`, `username` 키 추가
- 대시보드 탑바가 로그인 상태를 자동 반영

---

### `app_v2.py`

- `audit_logger` import 추가 (`try/except` 안전 처리)
- `page_home()` 에서 홈 대시보드 접근 시 세션당 1회 `PAGE_ACCESS` 감사 로그 기록

---

### 배포 체크리스트

- [ ] `DB_create.sql` 실행 (또는 `ALTER TABLE USERS ADD COLUMN IF NOT EXISTS military_rank ...` 마이그레이션)
- [ ] admin 계정 비밀번호 확인
- [ ] 테스트 계정 비밀번호 확인
- [ ] `AUDIT_LOG` 테이블 생성 확인
- [ ] `requirements.txt`에 인증 관련 의존성 확인

---

## v2.2
**마이페이지 도입 및 네비게이션 안정화**

### 1. 신규 기능: 마이페이지 (`pages/my_page.py`)
- **프로필 조회**: 현재 로그인한 사용자의 이름, 군번, 권한, ID 확인 가능
- **비밀번호 변경**: 현재 비밀번호 확인 후 새 비밀번호(8자 이상)로 변경 기능 추가
- **내 접속 기록**: 본인의 최근 접속 IP, 로그인/로그아웃 시간, 체류 시간(분) 조회 (최근 20건)
- **관리자 전용 기능**: `admin` 또는 `officer` 권한 계정 접속 시, 전체 사용자의 접속 로그 열람 탭 활성화 (최근 100건)

### 2. 네비게이션 & UI 개선
- **로그인 흐름 개선**: 로그인 성공 시 대시보드가 아닌 **마이페이지**로 먼저 이동하여 내 정보를 확인하도록 동선 변경
- **사이드바 개편**: 사이드바에 현재 접속 중인 OPERATOR 이름 표시 및 **MY PAGE** 버튼 추가로 언제든 마이페이지 접근 가능
- **StreamlitPageNotFoundError 해결**: `register_page.py`와 `delete_page.py`에서 `st.page_link`를 사용할 때 발생하던 에러를 해결하기 위해, `st.button` + `st.switch_page` 조합으로 모두 교체하여 안정적인 페이지 이동 보장

### 3. 코드 최적화 및 정리
- `app_v2.py`에 `register_page`와 `delete_page`를 미인증 상태의 `st.Page` 목록에 명시적으로 포함하여 라우팅 오류 원천 차단
- 불필요해진 `functions/navigation.py` 및 잔여 파일 완전 삭제

---

## v2.1
**코드 파편화 및 네비게이션 개편**

### 1. 코드 파편화 (모듈화)
- 기존 1,600줄에 달하던 `app_v2.py`를 기능별로 완전 분리하여 경량화
- **Python 함수 분리**: `functions/` 폴더 내 `dashboard_builder.py`, `data_functions.py`, `render_panels.py` 등 10여 개 모듈로 분리
- **CSS 모듈화**: `build_dashboard_css()` 내의 인라인 CSS를 역할별로 8개의 개별 `.css` 파일(`base.css`, `layout.css`, `animations.css` 등)로 분리

### 2. 네비게이션 구조 개편
- `st.navigation()` 공식 도입
- 미인증 상태에서는 로그인 페이지만 렌더링하고 사이드바를 완전히 숨김
- 인증 상태에서는 `홈페이지`, `훈련 가능 시간`, `체감온도 분석`, `특보 현황` 메뉴만 사이드바에 표시
- 회원가입/탈퇴 페이지는 사이드바 목록에서 완전히 숨김 처리

### 3. 무한 재귀 버그 수정
- `st.navigation()`에 진입점 파일을 등록할 때 발생하던 무한 재귀 실행 문제 해결
- 파일 경로 대신 **함수 참조(`st.Page(page_home)`)** 방식을 도입하여 재실행 없이 대시보드가 렌더링되도록 구조 개선
