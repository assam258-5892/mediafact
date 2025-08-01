#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import sqlite3
import markdown
from datetime import datetime
from mecab import MeCab
from flask import Flask, render_template, request, redirect, url_for, g

mecab = MeCab()

def mecab_morphs_text(text):
    return ' '.join(mecab.morphs(text))

DATABASE = 'db/mediafact.db'

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Jinja2 날짜 포맷 필터 등록
def datetime_format(value):
    try:
        dt = datetime.strptime(value[:16], '%Y-%m-%d %H:%M')
        return dt.strftime('%Y.%m.%d. %H:%M')
    except Exception:
        return value
app.jinja_env.filters['datetime_format'] = datetime_format

# DB 연결 함수
def get_db():
    if not hasattr(g, 'sqlite_db'):
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        g.sqlite_db = conn
    return g.sqlite_db

# 메인(최신 기사 목록)
@app.route('/')
def index():
    db = get_db()
    articles = db.execute('''
        SELECT 기사.*, 분류.분류명칭,
        (SELECT 사진경로 FROM 사진 WHERE 사진.기사번호 = 기사.기사번호 ORDER BY 사진.등록일자 ASC, 사진.사진번호 ASC LIMIT 1) AS 대표사진경로,
        기자.기자성명, 기자.기자직함
        FROM 기사
        JOIN 분류 ON 기사.분류번호 = 분류.분류번호
        JOIN 기자 ON 기사.기자번호 = 기자.기자번호
        WHERE 기사.공개여부=1
        ORDER BY 작성일자 DESC
        LIMIT 20
    ''').fetchall()
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('index.html', articles=articles, categories=categories)

# 기사 상세
@app.route('/article/<int:article_id>')
def article_detail(article_id):
    db = get_db()
    try:
        # 조회횟수 증가
        db.execute('UPDATE 기사 SET 조회횟수 = 조회횟수 + 1 WHERE 기사번호=?', (article_id,))
        db.commit()
        article = db.execute('SELECT 기사.*, 분류.분류명칭 FROM 기사 JOIN 분류 ON 기사.분류번호 = 분류.분류번호 WHERE 기사번호=? AND 기사.공개여부=1', (article_id,)).fetchone()
        photos = db.execute('SELECT * FROM 사진 WHERE 기사번호=?', (article_id,)).fetchall()
        reporter = db.execute('SELECT * FROM 기자 WHERE 기자번호=?', (article['기자번호'],)).fetchone() if article else None
        # 기사내용 [사진:N] 치환 후 마크다운 변환
        def replace_photo_tag(text, photos):
            def photo_replacer(match):
                num = int(match.group(1))
                for photo in photos:
                    if photo['사진번호'] == num:
                        filename = photo['사진경로'].split('/')[-1]
                        return f'<img src="/static/images/photo/{filename}" alt="사진:{num}" style="max-width:100%;">'
                return match.group(0)
            return re.sub(r'\[사진:(\d+)\]', lambda m: photo_replacer(m), text)
        if article and photos:
            replaced_content = replace_photo_tag(article['기사내용'], photos)
            article_content_html = markdown.markdown(replaced_content)
        else:
            article_content_html = markdown.markdown(article['기사내용']) if article else ''
    except Exception as e:
        article, photos, reporter, article_content_html = None, [], None, ''
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('article/index.html', article=article, photos=photos, reporter=reporter, categories=categories, article_content_html=article_content_html)

# 기사 편집
@app.route('/edit/<int:article_id>', methods=['GET', 'POST'])
def article_edit(article_id):
    db = get_db()
    if request.method == 'POST':
        title = request.form.get('title', '')
        subtitle = request.form.get('subtitle', '')
        summary = request.form.get('summary', '')
        content = request.form.get('content', '')
        publish = int(request.form.get('publish', 0))
        category = int(request.form.get('category', 0))
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute('UPDATE 기사 SET 기사제목=?, 기사부제=?, 기사요약=?, 기사내용=?, 공개여부=?, 분류번호=?, 수정일자=? WHERE 기사번호=?',
                   (title, subtitle, summary, content, publish, category, now, article_id))
        # 형태소 분석 후 색인 테이블에 저장
        db.execute('REPLACE INTO 기사전문색인 (기사번호, 기사제목, 기사부제, 기사요약, 기사내용) VALUES (?, ?, ?, ?, ?)',
                   (article_id,
                    mecab_morphs_text(title),
                    mecab_morphs_text(subtitle),
                    mecab_morphs_text(summary),
                    mecab_morphs_text(content)))
        photos = db.execute('SELECT 사진연번, 사진설명 FROM 사진 WHERE 기사번호=?', (article_id,)).fetchall()
        for photo in photos:
            db.execute('REPLACE INTO 사진전문색인 (사진연번, 사진설명, 기사제목, 기사부제, 기사요약, 기사내용) VALUES (?, ?, ?, ?, ?, ?)',
                       (photo['사진연번'],
                        mecab_morphs_text(photo['사진설명']),
                        mecab_morphs_text(title),
                        mecab_morphs_text(subtitle),
                        mecab_morphs_text(summary),
                        mecab_morphs_text(content)))
        db.commit()
        return redirect(url_for('article_detail', article_id=article_id))
    article = db.execute('SELECT * FROM 기사 WHERE 기사번호=?', (article_id,)).fetchone()
    photos = db.execute('SELECT * FROM 사진 WHERE 기사번호=?', (article_id,)).fetchall()
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('article/edit.html', article=article, categories=categories, photos=photos)

# 분류별 기사
@app.route('/category/<int:category_id>')
def category(category_id):
    db = get_db()
    articles = db.execute('''
        SELECT 기사.*, 기사.기사부제, 기사.기사요약, 분류.분류명칭, 기자.기자성명, 기자.기자직함,
        (SELECT 사진경로 FROM 사진 WHERE 사진.기사번호 = 기사.기사번호 ORDER BY 사진.등록일자 ASC, 사진.사진번호 ASC LIMIT 1) AS 대표사진경로
        FROM 기사
        JOIN 분류 ON 기사.분류번호 = 분류.분류번호
        JOIN 기자 ON 기사.기자번호 = 기자.기자번호
        WHERE 기사.분류번호=? AND 기사.공개여부=1
        ORDER BY 작성일자 DESC
    ''', (category_id,)).fetchall()
    category_info = db.execute('SELECT * FROM 분류 WHERE 분류번호=?', (category_id,)).fetchone()
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('category/index.html', articles=articles, category_info=category_info, categories=categories, category_id=category_id)

# 기자별 기사
@app.route('/reporter/<int:reporter_id>')
def reporter(reporter_id):
    db = get_db()
    articles = db.execute('''
        SELECT 기사.*, 기사.기사부제, 기사.기사요약, 분류.분류명칭, 기자.기자성명, 기자.기자직함,
        (SELECT 사진경로 FROM 사진 WHERE 사진.기사번호 = 기사.기사번호 ORDER BY 사진.등록일자 ASC, 사진.사진번호 ASC LIMIT 1) AS 대표사진경로
        FROM 기사
        JOIN 분류 ON 기사.분류번호 = 분류.분류번호
        JOIN 기자 ON 기사.기자번호 = 기자.기자번호
        WHERE 기자.기자번호=? AND 기사.공개여부=1
        ORDER BY 작성일자 DESC
    ''', (reporter_id,)).fetchall()
    reporter = db.execute('SELECT * FROM 기자 WHERE 기자번호=?', (reporter_id,)).fetchone()
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('reporter/index.html', articles=articles, reporter=reporter, categories=categories, reporter_id=reporter_id)

# 사진 갤러리
@app.route('/photo')
def photo_gallery():
    db = get_db()
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    total = db.execute('SELECT COUNT(*) FROM 사진').fetchone()[0]
    total_page = (total + per_page - 1) // per_page
    photos = db.execute('SELECT * FROM 사진 ORDER BY 등록일자 DESC LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('photo/index.html', photos=photos, categories=categories, page=page, total_page=total_page, search_type='photo')

# 사진 상세
@app.route('/photo/<int:photo_id>')
def photo_detail(photo_id):
    db = get_db()
    photo = db.execute('SELECT * FROM 사진 WHERE 사진연번=?', (photo_id,)).fetchone()
    article = db.execute('SELECT 기사제목, 기사부제, 기사요약, 기사번호 FROM 기사 WHERE 기사번호=?', (photo['기사번호'],)).fetchone() if photo else None
    reporter = db.execute('SELECT * FROM 기자 WHERE 기자번호=?', (photo['기자번호'],)).fetchone() if photo else None
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('photo/detail.html', photo=photo, article=article, reporter=reporter, categories=categories, search_type='photo')

# 기사 검색(FTS5)
@app.route('/search')
def search():
    query = request.args.get('q', '')
    db = get_db()
    articles = []
    photos = []
    search_type = request.args.get('type', '')
    category_id = request.args.get('category_id')
    reporter_id = request.args.get('reporter_id')
    if query:
        morph_query = mecab_morphs_text(query)
        try:
            if search_type == 'photo':
                # 사진 검색만 (분류 제한 없음)
                sql_photo = '''
                    SELECT DISTINCT 사진.*, 기사.기사제목, 기사.기사부제, 기사.기사요약, 기사.기사내용
                    FROM 사진전문색인
                    JOIN 사진 ON 사진전문색인.사진연번 = 사진.사진연번
                    JOIN 기사 ON 사진.기사번호 = 기사.기사번호
                    WHERE 사진전문색인 MATCH ? AND 사진.삭제여부=0
                    ORDER BY 사진.등록일자 DESC
                '''
                photos = db.execute(sql_photo, (morph_query,)).fetchall()
            else:
                # 기사 검색만
                sql_article = '''
                    SELECT DISTINCT 기사.*, 기사.기사부제, 기사.기사요약, 분류.분류명칭, 기자.기자성명, 기자.기자직함,
                    (SELECT 사진경로 FROM 사진 WHERE 사진.기사번호 = 기사.기사번호 ORDER BY 사진.등록일자 ASC, 사진.사진번호 ASC LIMIT 1) AS 대표사진경로
                    FROM 기사전문색인
                    JOIN 기사 ON 기사전문색인.기사번호 = 기사.기사번호
                    JOIN 분류 ON 기사.분류번호 = 분류.분류번호
                    JOIN 기자 ON 기사.기자번호 = 기자.기자번호
                    WHERE 기사전문색인 MATCH ? AND 기사.공개여부=1
                    {cat_filter}
                    {reporter_filter}
                    ORDER BY 기사.작성일자 DESC
                '''.replace('{cat_filter}', 'AND 기사.분류번호=?' if category_id else '').replace('{reporter_filter}', 'AND 기자.기자번호=?' if reporter_id else '')
                params = [morph_query]
                if category_id:
                    params.append(category_id)
                if reporter_id:
                    params.append(reporter_id)
                articles = db.execute(sql_article, tuple(params)).fetchall()
        except Exception as e:
            articles = []
            photos = []
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    category = db.execute('SELECT * FROM 분류 WHERE 분류번호=?', (category_id,)).fetchone() if category_id else None
    reporter = db.execute('SELECT * FROM 기자 WHERE 기자번호=?', (reporter_id,)).fetchone() if reporter_id else None
    return render_template('search/index.html', articles=articles, photos=photos, query=query, categories=categories, category=category, reporter=reporter, search_type=search_type, category_id=category_id, reporter_id=reporter_id )

# 전체 기사/사진 색인 재생성 (관리자용)
@app.route('/reindex')
def admin_reindex():
    db = get_db()
    # 색인 테이블 비우기
    db.execute('DELETE FROM 기사전문색인')
    db.execute('DELETE FROM 사진전문색인')
    # 기사 색인
    articles = db.execute('SELECT 기사번호, 기사제목, 기사부제, 기사요약, 기사내용 FROM 기사').fetchall()
    for a in articles:
        db.execute('REPLACE INTO 기사전문색인 (기사번호, 기사제목, 기사부제, 기사요약, 기사내용) VALUES (?, ?, ?, ?, ?)',
                   (a['기사번호'],
                    mecab_morphs_text(a['기사제목'] or ''),
                    mecab_morphs_text(a['기사부제'] or ''),
                    mecab_morphs_text(a['기사요약'] or ''),
                    mecab_morphs_text(a['기사내용'] or '')))
    # 사진 색인
    photos = db.execute('SELECT 사진연번, 사진설명, 기사번호 FROM 사진').fetchall()
    for p in photos:
        # 기사 정보 가져오기
        a = db.execute('SELECT 기사제목, 기사부제, 기사요약, 기사내용 FROM 기사 WHERE 기사번호=?', (p['기사번호'],)).fetchone()
        db.execute('REPLACE INTO 사진전문색인 (사진연번, 사진설명, 기사제목, 기사부제, 기사요약, 기사내용) VALUES (?, ?, ?, ?, ?, ?)',
                   (p['사진연번'],
                    mecab_morphs_text(p['사진설명'] or ''),
                    mecab_morphs_text(a['기사제목'] if a else ''),
                    mecab_morphs_text(a['기사부제'] if a else ''),
                    mecab_morphs_text(a['기사요약'] if a else ''),
                    mecab_morphs_text(a['기사내용'] if a else '')))
    db.commit()
    return '색인 재생성 완료!'

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

if __name__ == '__main__':
    app.run(debug=True)
