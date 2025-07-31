-- MediaFact 데이터베이스 스키마
-- 이 스키마는 기사, 분류, 기자, 사진 정보를 관리하는 구조를 정의합니다.

-- 데이터베이스 구조도
--
-- [분류]───┐
--          │
--          ▼
--       [기사]─────┐
--          │       │
--          ▼       ▼
--       [사진]  [기자]
--          ▲       ▲
--          └───────┘

-- 기사 분류(카테고리) 관리 테이블
CREATE TABLE IF NOT EXISTS 분류 (
    분류번호 INTEGER PRIMARY KEY AUTOINCREMENT, -- 분류 고유번호
    분류명칭 TEXT NOT NULL, -- 분류명칭(예: 정치, 경제, 사회 등)
    분류설명 TEXT -- 분류에 대한 설명
);

-- 기사/사진 작성자(기자) 정보 테이블
CREATE TABLE IF NOT EXISTS 기자 (
    기자번호 INTEGER PRIMARY KEY AUTOINCREMENT, -- 기자 고유번호
    기자성명 TEXT NOT NULL, -- 기자 이름
    기자직함 TEXT, -- 기자 직함(예: 기자, 대표기자, 편집장 등)
    메일주소 TEXT, -- 이메일 주소
    암호해시 TEXT -- 비밀번호 해시값(로그인용)
);

-- 기사 정보 테이블
CREATE TABLE IF NOT EXISTS 기사 (
    기사번호 INTEGER PRIMARY KEY AUTOINCREMENT, -- 기사 고유번호
    분류번호 INTEGER NOT NULL, -- 분류 테이블 참조
    기자번호 INTEGER NOT NULL, -- 기자 테이블 참조
    대표사진 INTEGER, -- 대표 사진번호(기사 내 사진번호)
    기사제목 TEXT NOT NULL, -- 기사 제목
    기사부제 TEXT, -- 기사 부제
    기사요약 TEXT, -- 기사 요약
    기사내용 TEXT NOT NULL, -- 기사 본문(마크다운 등)
    작성일자 TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 최초 작성일
    수정일자 TIMESTAMP, -- 마지막 수정일
    게시여부 INTEGER DEFAULT 0, -- 0: 비공개, 1: 공개
    삭제여부 INTEGER DEFAULT 0, -- 0: 정상, 1: 삭제됨
    FOREIGN KEY (분류번호) REFERENCES 분류(분류번호),
    FOREIGN KEY (기자번호) REFERENCES 기자(기자번호)
);

-- 기사에 포함된 사진 정보 테이블 (기사별 다수 사진 가능)
CREATE TABLE IF NOT EXISTS 사진 (
    사진연번 INTEGER PRIMARY KEY AUTOINCREMENT, -- 전체 사진 고유번호
    기사번호 INTEGER NOT NULL, -- 기사 테이블 참조
    기자번호 INTEGER NOT NULL, -- 기자 테이블 참조
    사진번호 INTEGER NOT NULL, -- 기사 내 사진번호(순번, 1부터)
    사진경로 TEXT NOT NULL, -- 파일 경로(16진수 디렉토리 구조 등)
    사진설명 TEXT, -- 사진 설명(검색/관리용)
    등록일자 TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 사진 등록일
    삭제여부 INTEGER DEFAULT 0, -- 0: 정상, 1: 삭제됨
    FOREIGN KEY (기사번호) REFERENCES 기사(기사번호) ON DELETE CASCADE,
    FOREIGN KEY (기자번호) REFERENCES 기자(기자번호),
    UNIQUE (기사번호, 사진번호)
);
