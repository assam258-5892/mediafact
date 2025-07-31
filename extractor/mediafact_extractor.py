#!/usr/bin/python3
# -*- coding: utf-8  -*-
"""
1.html을 참조하여 기사 제목, 본문, 대표사진(이미지), 기자명, 날짜를 추출하는 코드 예시
"""
from bs4 import BeautifulSoup
import os

def extract_article_from_html(html_path):
    if not os.path.exists(html_path):
        print(f"파일 없음: {html_path}")
        return None
    # 파일명에서 원 기사번호 추출
    import re
    m = re.search(r'(\d+)\.html$', html_path)
    원기사번호 = int(m.group(1)) if m else None
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')

    # 제목 추출
    title_tag = soup.find('div', class_='art_vt_la1')
    title = title_tag.get_text(strip=True) if title_tag else ''

    # 소제목 추출
    subtitle_tag = soup.find('div', class_='art_vt_me1')
    subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else ''

    # 본문 추출 (id='contents' 내부 텍스트)
    contents = soup.find('div', id='contents')
    content = contents.get_text(separator='\n', strip=True) if contents else ''

    # 본문 문단 리스트 추출 (id='contents' 내부 div + 직접 포함된 텍스트)
    paragraphs = []
    if contents:
        # 직접 포함된 텍스트(자식 div가 아닌 텍스트 노드)도 추가
        from bs4 import NavigableString
        for child in contents.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    paragraphs.append(text)
        # 내부 div의 텍스트도 추가
        for div in contents.find_all('div'):
            text = div.get_text(strip=True)
            if text:
                paragraphs.append(text)

    # 본문 내 모든 이미지 src와 alt(설명) 추출
    img_tags = contents.find_all('img') if contents else []
    images = []
    for img in img_tags:
        src = img['src'] if img.has_attr('src') else None
        alt = img.get('alt', '')
        if src:
            images.append({'src': src, 'alt': alt})

    # 대표사진 추출 (첫 번째 img 또는 alt에 '대표'/'main' 등 포함)
    main_image = None
    for img in images:
        if '대표' in img['alt'].lower() or 'main' in img['alt'].lower():
            main_image = img['src']
            break
    if not main_image and images:
        main_image = images[0]['src']  # alt 조건 없으면 첫 번째 이미지

    # 기자 정보 추출 (class='name1' 내부 a 태그)
    name_div = soup.find('div', class_='name1')
    기자성명 = ''
    기자직함 = ''
    메일주소 = ''
    if name_div:
        a_tag = name_div.find('a')
        if a_tag:
            text = a_tag.get_text(strip=True)
            # 예: "방채영  대표기자 기자[press.darak@gmail.com]"
            import re
            # 기자성명: 한글 이름만 추출, 기자직함: 대표기자 등만 추출
            match = re.match(r'([가-힣]+)\s*([^\[]*)\[([^\]]+)\]', text)
            if match:
                기자성명 = match.group(1).strip()
                기자직함 = match.group(2).replace('기자', '').replace('대표', '대표기자').strip()
                if not 기자직함:
                    기자직함 = '기자'
                메일주소 = match.group(3).strip()
            else:
                기자성명 = text
                기자직함 = ''
                메일주소 = ''

    # 날짜 추출 (class='date1')
    date_div = soup.find('div', class_='date1')
    date = ''
    if date_div:
        import re
        from datetime import datetime
        date_text = date_div.get_text(strip=True)
        # 예: '글쓴날 : [24-12-26 21:24]'
        match = re.search(r"\[(\d{2})-(\d{2})-(\d{2}) (\d{2}):(\d{2})\]", date_text)
        if match:
            year = int(match.group(1)) + 2000
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            dt = datetime(year, month, day, hour, minute)
            date = dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            date = date_text

    print(f"기사제목: {title}")
    print(f"기사부제: {subtitle}")
    print(f"작성일자: {date}")
    print(f"기자성명: {기자성명}")
    print(f"기자직함: {기자직함}")
    print(f"메일주소: {메일주소}")
    print(f"대표사진: {main_image}")
    print("사진목록:")
    for img in images:
        print(f"  - src: {img['src']}, alt: {img['alt']}")
    print(f"기사내용:\n{content}")
    print("문단 리스트:")
    for p in paragraphs:
        print(f"  - {p}")
    return {
        '기사제목': title,
        '기사부제': subtitle,
        '작성일자': date,
        '기자성명': 기자성명,
        '기자직함': 기자직함,
        '메일주소': 메일주소,
        '대표사진': main_image,
        '사진목록': images,
        '기사내용': content,
        '문단리스트': paragraphs,
        '원기사번호': 원기사번호
    }

if __name__ == '__main__':

    html_files = [f'captured/{i}.html' for i in [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 13, 16, 17, 26, 29]]
    articles = []
    for html_path in html_files:
        print(f"\n==== {html_path} ====")
        result = extract_article_from_html(html_path)
        if result:
            articles.append(result)
    # articles 리스트에 모든 추출 결과가 저장됨
    # 이후 DB INSERT 등 활용 가능

    # 기자 정보 중복 제거 및 INSERT 문 생성 예시
    unique_reporters = {}
    reporter_seq = 1
    reporter_number_map = {}
    for article in articles:
        key = (article['기자성명'], article['기자직함'], article['메일주소'])
        if article['기자성명'] and key not in unique_reporters:
            unique_reporters[key] = True
            reporter_number_map[key] = reporter_seq
            reporter_seq += 1

    # 기사번호와 분류코드 매핑 (예시)
    article_category_map = {
        1: 7,   # 방송,문화
        2: 7,   # 방송,문화
        4: 1,   # 미디어시대
        5: 4,   # 국제
        6: 5,   # 종교
        7: 5,   # 종교
        8: 5,   # 종교
        9: 1,   # 미디어시대
        10: 2,  # 정치
        11: 8,  # 건강
        13: 5,  # 종교
        16: 5,  # 종교
        17: 2,  # 정치
        26: 5,  # 종교
        29: 5   # 종교
    }

    # SQL INSERT 문을 dump.sql 파일에 저장
    with open('dump.sql', 'w', encoding='utf-8') as sql_file:
        # 분류 테이블
        sql_file.write('-- 분류 테이블\n')
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (1, '미디어시대');\n")
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (2, '정치');\n")
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (3, '경제');\n")
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (4, '국제');\n")
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (5, '종교');\n")
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (6, '사회');\n")
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (7, '방송,문화');\n")
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (8, '건강');\n")
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (9, '지역');\n")
        sql_file.write("INSERT INTO 분류 (분류번호, 분류명칭) VALUES (10, '오피니언');\n")
        sql_file.write('\n')

        # 기자 테이블
        sql_file.write('-- 기자 테이블\n')
        for reporter in unique_reporters:
            기자성명, 기자직함, 메일주소 = reporter
            기자번호 = reporter_number_map[reporter]
            sql_file.write(f"INSERT INTO 기자 (기자번호, 기자성명, 기자직함, 메일주소) VALUES ({기자번호}, '{기자성명}', '{기자직함}', '{메일주소}');\n")
        sql_file.write('\n')

        # 기사 테이블
        sql_file.write('-- 기사 테이블\n')
        main_photo_seq_list = []  # 각 기사별 대표사진의 사진연번 저장
        photo_seq = 1
        for article in articles:
            main_image_src = article['대표사진']
            main_photo_seq = None
            # 사진연번 계산을 위해 사진목록 먼저 순회
            for photo_idx, photo in enumerate(article['사진목록'], start=1):
                is_main = (photo['src'] == main_image_src)
                if is_main:
                    main_photo_seq = photo_seq + photo_idx - 1
            main_photo_seq_list.append(main_photo_seq)
        for i, article in enumerate(articles):
            main_photo_seq = main_photo_seq_list[i]
            기사번호 = article['원기사번호']
            분류번호 = article_category_map.get(기사번호, 1)  # 매핑 없으면 1(기본값)
            기사제목 = article['기사제목'].replace("'", "''")
            기사부제 = article['기사부제'].replace("'", "''")
            기사내용 = article['기사내용'].replace("'", "''")
            key = (article['기자성명'], article['기자직함'], article['메일주소'])
            기자번호 = reporter_number_map.get(key, 1)
            sql_file.write(f"INSERT INTO 기사 (기사번호, 분류번호, 기자번호, 대표사진, 기사제목, 기사부제, 기사내용, 작성일자) VALUES ({기사번호}, {분류번호}, {기자번호}, {main_photo_seq if main_photo_seq else 'NULL'}, '{기사제목}', '{기사부제}', '{기사내용}', '{article['작성일자']}');\n")
        sql_file.write('\n')

        # 사진 테이블
        sql_file.write('-- 사진 테이블\n')
        import re
        photo_seq = 1
        for i, article in enumerate(articles):
            기사번호 = article['원기사번호']
            등록일자 = article['작성일자']
            key = (article['기자성명'], article['기자직함'], article['메일주소'])
            기자번호 = reporter_number_map.get(key, 1)
            for photo_idx, photo in enumerate(article['사진목록'], start=1):
                src = photo['src']
                import os
                ext = os.path.splitext(src)[1] if '.' in os.path.basename(src) else '.jpg'
                filename = f"{기사번호}_{photo_idx}{ext}"
                alt_text = re.sub(r'\s+', ' ', photo['alt'].strip()).replace("'", "''")
                sql_file.write(f"INSERT INTO 사진 (사진연번, 기사번호, 기자번호, 사진번호, 사진경로, 사진설명, 등록일자) VALUES ({photo_seq}, {기사번호}, {기자번호}, {photo_idx}, '{filename}', '{alt_text}', '{등록일자}');\n")
                photo_seq += 1
        sql_file.write('\n')

        # sqlite_sequence 테이블
        sql_file.write('-- sqlite_sequence 테이블\n')
        last_reporter_id = len(unique_reporters)
        last_article_id = max(article['원기사번호'] for article in articles)
        last_photo_id = photo_seq - 1
        last_category_id = 10
        sql_file.write(f"UPDATE sqlite_sequence SET seq = {last_category_id} WHERE name = '분류';\n")
        sql_file.write(f"UPDATE sqlite_sequence SET seq = {last_reporter_id} WHERE name = '기자';\n")
        sql_file.write(f"UPDATE sqlite_sequence SET seq = {last_article_id} WHERE name = '기사';\n")
        sql_file.write(f"UPDATE sqlite_sequence SET seq = {last_photo_id} WHERE name = '사진';\n")
        sql_file.write('\n')

    print("SQL INSERT 문이 dump.sql 파일에 저장되었습니다.")

    # 사진 다운로드용 curl 명령을 download.sh 파일에 저장
    with open('download.sh', 'w', encoding='utf-8') as sh_file:
        sh_file.write("#!/bin/bash\n\n")
        sh_file.write("# 사진 다운로드 스크립트\n")
        sh_file.write("mkdir -p photo\n\n")
        base_url = "http://www.the-mediafact.com"
        for i, article in enumerate(articles):
            기사번호 = article['원기사번호']
            for photo_idx, photo in enumerate(article['사진목록'], start=1):
                src = photo['src']
                import os
                ext = os.path.splitext(src)[1] if '.' in os.path.basename(src) else '.jpg'
                filename = f"photo/{기사번호}_{photo_idx}{ext}"
                # src가 // 또는 http로 시작하지 않으면 base_url 붙임
                if src.startswith('//'):
                    full_url = 'http:' + src
                elif src.startswith('http'):
                    full_url = src
                else:
                    full_url = base_url + src if src.startswith('/') else base_url + '/' + src
                sh_file.write(f"curl -L '{full_url}' -o '{filename}'\n")

    # 실행 권한 부여
    os.chmod('download.sh', 0o755)

    print("사진 다운로드 스크립트가 download.sh 파일에 저장되고 실행 권한이 부여되었습니다.")
