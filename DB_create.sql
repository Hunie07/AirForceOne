-- =========================================================
-- W-BOSS Database Schema
-- 사용하지 않는 테이블 제거 버전
-- 제거 대상:
--   1) spatial_boundary
--   2) asos_station
--   3) asos_history
-- =========================================================

CREATE DATABASE IF NOT EXISTS weather_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE weather_db;

-- ---------------------------------------------------------
-- 1. 지역 마스터
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS region (
    region_id    INT NOT NULL AUTO_INCREMENT COMMENT '지역 PK',
    region_name  VARCHAR(50) NOT NULL COMMENT '지역명',
    province     VARCHAR(50) NOT NULL COMMENT '시/도',
    PRIMARY KEY (region_id),
    INDEX idx_province (province)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='지역 기준 정보';

-- ---------------------------------------------------------
-- 2. 부대 마스터
-- users.unit_id 의 참조 대상
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS unit (
    unit_id    VARCHAR(20) NOT NULL COMMENT '부대 코드 PK',
    region_id  INT NOT NULL COMMENT '소속 지역 ID',
    unit_name  VARCHAR(100) NOT NULL COMMENT '부대명',
    PRIMARY KEY (unit_id),
    CONSTRAINT fk_unit_region
        FOREIGN KEY (region_id) REFERENCES region(region_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='부대 기준 정보';

-- ---------------------------------------------------------
-- 3. 단기예보 저장 테이블
-- best_train_time / forecast pipeline 용
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS forecast_data (
    id                   BIGINT NOT NULL AUTO_INCREMENT COMMENT '예보 PK',
    region               VARCHAR(50) NOT NULL COMMENT '지역명',
    forecast_base_time   DATETIME NOT NULL COMMENT '예보 발표 기준 시각',
    forecast_target_time DATETIME NOT NULL COMMENT '예보 대상 시각',
    tmp                  DECIMAL(5,1) COMMENT '기온',
    wsd                  DECIMAL(5,1) COMMENT '풍속',
    reh                  DECIMAL(5,1) COMMENT '습도',
    pcp                  DECIMAL(6,1) COMMENT '강수량',
    apparent_temp        DECIMAL(5,1) COMMENT '체감온도',
    heat_index           DECIMAL(5,1) COMMENT '온도지수',
    PRIMARY KEY (id),
    UNIQUE KEY uq_region_base_target (region, forecast_base_time, forecast_target_time)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='단기예보 수집 결과 저장';

-- ---------------------------------------------------------
-- 4. 기상특보 저장 테이블
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS weather_alert (
    id                    INT NOT NULL AUTO_INCREMENT COMMENT '특보 PK',
    brnch                 VARCHAR(30) COMMENT '지점/지청 코드',
    wrn                   VARCHAR(5) COMMENT '특보 코드',
    lvl                   VARCHAR(5) COMMENT '레벨 코드',
    cmd                   VARCHAR(5) COMMENT '명령 코드',
    ttl                   VARCHAR(200) NOT NULL COMMENT '제목',
    prsntn_tm             VARCHAR(30) NOT NULL COMMENT '발표 시각 원문',
    frmnt_tm              VARCHAR(30) COMMENT '발효 시각 원문',
    tm_in                 VARCHAR(20) COMMENT '입력 시각 원문',
    spne_frmnt_prcon_cn   TEXT COMMENT '발효 조건 내용',
    rlvt_zone             TEXT COMMENT '관련 지역',
    reg_id                VARCHAR(20) COMMENT '지역 코드',
    alert_type            VARCHAR(30) COMMENT '가공 특보 유형',
    alert_level           VARCHAR(20) COMMENT '가공 특보 단계',
    status                VARCHAR(10) NOT NULL DEFAULT 'ACTIVE' COMMENT '상태',
    collected_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '수집 시각',
    PRIMARY KEY (id),
    UNIQUE KEY uq_alert (reg_id, wrn, prsntn_tm, cmd),
    INDEX idx_status (status),
    INDEX idx_reg_id (reg_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='기상특보 원문 및 가공 결과 저장';

-- ---------------------------------------------------------
-- 5. 사용자 테이블
-- 현재 프로젝트는 평문 비밀번호 비교 구조
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id         INT NOT NULL AUTO_INCREMENT COMMENT '사용자 PK',
    unit_id         VARCHAR(20) NOT NULL COMMENT '소속 부대 코드',
    username        VARCHAR(20) NOT NULL COMMENT '이름',
    service_number  VARCHAR(20) NOT NULL COMMENT '군번(로그인 ID 역할)',
    password        VARCHAR(255) NOT NULL COMMENT '비밀번호(현재 평문 구조)',
    role            ENUM('admin','officer','nco','soldier') NOT NULL DEFAULT 'soldier' COMMENT '권한 역할',
    military_rank   VARCHAR(50) DEFAULT NULL COMMENT '계급',
    deleted_at      DATETIME DEFAULT NULL COMMENT '탈퇴/비활성 시각',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시각',
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_service_number (service_number),
    CONSTRAINT fk_users_unit
        FOREIGN KEY (unit_id) REFERENCES unit(unit_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='회원 정보';

-- ---------------------------------------------------------
-- 6. 접속 로그
-- 로그인/로그아웃 이력 저장
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS access_log (
    log_id           BIGINT NOT NULL AUTO_INCREMENT COMMENT '접속 로그 PK',
    user_id          INT NOT NULL COMMENT '사용자 ID',
    service_number   VARCHAR(20) NOT NULL COMMENT '군번',
    unit_id          VARCHAR(20) NOT NULL COMMENT '부대 코드',
    ip_address       VARCHAR(64) DEFAULT NULL COMMENT '접속 IP',
    user_agent       VARCHAR(255) DEFAULT NULL COMMENT '브라우저/기기 정보',
    session_id       VARCHAR(128) DEFAULT NULL COMMENT '세션 ID',
    login_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '로그인 시각',
    logout_at        DATETIME DEFAULT NULL COMMENT '로그아웃 시각',
    PRIMARY KEY (log_id),
    INDEX idx_access_user (user_id, login_at),
    INDEX idx_access_sn (service_number, login_at),
    CONSTRAINT fk_access_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='접속 이력';

-- ---------------------------------------------------------
-- 7. 감사 로그
-- 회원정보 변경, 가입, 탈퇴 등 행위 기록
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id         BIGINT NOT NULL AUTO_INCREMENT COMMENT '감사 로그 PK',
    user_id          INT DEFAULT NULL COMMENT '사용자 ID',
    service_number   VARCHAR(20) DEFAULT NULL COMMENT '군번',
    action_type      VARCHAR(40) NOT NULL COMMENT '행위 유형',
    page             VARCHAR(100) DEFAULT NULL COMMENT '발생 페이지',
    before_data      JSON DEFAULT NULL COMMENT '변경 전 데이터',
    after_data       JSON DEFAULT NULL COMMENT '변경 후 데이터',
    description      VARCHAR(255) DEFAULT NULL COMMENT '설명',
    ip_address       VARCHAR(64) DEFAULT NULL COMMENT '접속 IP',
    device_info      VARCHAR(255) DEFAULT NULL COMMENT '기기 정보',
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '기록 시각',
    PRIMARY KEY (audit_id),
    INDEX idx_audit_user (user_id, created_at),
    INDEX idx_audit_sn (service_number, created_at),
    INDEX idx_audit_action (action_type, created_at)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='감사 로그';

-- ---------------------------------------------------------
-- 초기 데이터
-- ---------------------------------------------------------
INSERT IGNORE INTO region (region_id, region_name, province) VALUES
    (1, '연천군', '경기도'),
    (2, '철원군', '강원도'),
    (3, '화천군', '강원도'),
    (4, '양구군', '강원도'),
    (5, '고성군', '강원도');

INSERT IGNORE INTO unit (unit_id, region_id, unit_name) VALUES
    ('HQ01', 1, '공군본부 기상단'),
    ('1BON', 1, '제1전투비행단'),
    ('2BON', 2, '제2전투비행단'),
    ('3BON', 3, '제3전투비행단'),
    ('4BON', 4, '제4전투비행단'),
    ('5BON', 5, '제5전투비행단');

INSERT IGNORE INTO users (unit_id, username, service_number, password, role, military_rank)
VALUES ('HQ01', '관리자', '99-99999', 'acorn1234', 'admin', '대위');

-- ---------------------------------------------------------
-- 확인용 조회 예시
-- ---------------------------------------------------------
-- SELECT * FROM users;
-- SELECT * FROM access_log ORDER BY login_at DESC;
-- SELECT * FROM audit_log ORDER BY created_at DESC;
-- SELECT * FROM forecast_data ORDER BY forecast_base_time DESC;
-- SELECT * FROM weather_alert ORDER BY collected_at DESC;