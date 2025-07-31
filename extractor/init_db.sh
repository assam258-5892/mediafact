#!/bin/bash
# 미디어팩트 DB 초기화 스크립트
# DB 파일: ../db/mediafact.db

DB_PATH="../db/mediafact.db"
SCHEMA_PATH="../db/schema.sql"
DUMP_PATH="../extractor/dump.sql"
SUMMARY_PATH="../extractor/summary.sql"

# 1. 기존 DB 삭제
if [ -f "$DB_PATH" ]; then
    echo "기존 DB 파일 삭제: $DB_PATH"
    rm "$DB_PATH"
fi

# 2. 새 DB 생성 및 스키마 적용
echo "새 DB 생성 및 스키마 적용..."
sqlite3 "$DB_PATH" < "$SCHEMA_PATH"

# 3. 데이터 INSERT
if [ -f "$DUMP_PATH" ]; then
    echo "데이터 INSERT..."
    sqlite3 "$DB_PATH" < "$DUMP_PATH"
else
    echo "데이터 파일이 없습니다: $DUMP_PATH"
fi

# 3-1. 기사요약 업데이트
if [ -f "$SUMMARY_PATH" ]; then
    echo "기사요약 업데이트..."
    sqlite3 "$DB_PATH" < "$SUMMARY_PATH"
else
    echo "기사요약 파일이 없습니다: $SUMMARY_PATH"
fi

echo "DB 초기화 완료: $DB_PATH"

# 4. 사진 파일 복제
PHOTO_SRC="../extractor/photo"
PHOTO_DST="../static/images/photo"
echo "사진 파일 복제: $PHOTO_SRC -> $PHOTO_DST"
mkdir -p "$PHOTO_DST"
cp -a "$PHOTO_SRC/." "$PHOTO_DST/"
