from flask import Flask, render_template, request, redirect, url_for, g
from datetime import datetime
import sqlite3

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
    articles = db.execute('SELECT 기사.*, 분류.분류명칭 FROM 기사 JOIN 분류 ON 기사.분류번호 = 분류.분류번호 ORDER BY 작성일자 DESC LIMIT 20').fetchall()
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
        article = db.execute('SELECT 기사.*, 분류.분류명칭 FROM 기사 JOIN 분류 ON 기사.분류번호 = 분류.분류번호 WHERE 기사번호=?', (article_id,)).fetchone()
        photos = db.execute('SELECT * FROM 사진 WHERE 기사번호=?', (article_id,)).fetchall()
        reporter = db.execute('SELECT * FROM 기자 WHERE 기자번호=?', (article['기자번호'],)).fetchone() if article else None
    except Exception as e:
        article, photos, reporter = None, [], None
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('article.html', article=article, photos=photos, reporter=reporter, categories=categories)

# 카테고리별 기사
@app.route('/category/<int:category_id>')
def category(category_id):
    db = get_db()
    articles = db.execute('SELECT 기사.*, 분류.분류명칭 FROM 기사 JOIN 분류 ON 기사.분류번호 = 분류.분류번호 WHERE 기사.분류번호=? ORDER BY 작성일자 DESC', (category_id,)).fetchall()
    category_info = db.execute('SELECT * FROM 분류 WHERE 분류번호=?', (category_id,)).fetchone()
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('category.html', articles=articles, category_info=category_info, categories=categories)

# 기자별 기사
@app.route('/reporter/<int:reporter_id>')
def reporter(reporter_id):
    db = get_db()
    articles = db.execute('SELECT 기사.*, 분류.분류명칭 FROM 기사 JOIN 분류 ON 기사.분류번호 = 분류.분류번호 WHERE 기자번호=? ORDER BY 작성일자 DESC', (reporter_id,)).fetchall()
    reporter = db.execute('SELECT * FROM 기자 WHERE 기자번호=?', (reporter_id,)).fetchone()
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('reporter.html', articles=articles, reporter=reporter, categories=categories)

# 사진 갤러리
@app.route('/photo')
def photo_gallery():
    db = get_db()
    photos = db.execute('SELECT * FROM 사진 ORDER BY 등록일자 DESC').fetchall()
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('photo.html', photos=photos, categories=categories)

# 기사 검색(FTS5)
@app.route('/search')
def search():
    query = request.args.get('q', '')
    db = get_db()
    articles = []
    if query:
        try:
            sql = '''SELECT 기사.*, 분류.분류명칭 FROM 기사전문색인 JOIN 기사 ON 기사전문색인.기사번호 = 기사.기사번호 JOIN 분류 ON 기사.분류번호 = 분류.분류번호 WHERE 기사전문색인 MATCH ? ORDER BY 기사.작성일자 DESC'''
            articles = db.execute(sql, (query,)).fetchall()
        except Exception as e:
            articles = []
    categories = db.execute('SELECT * FROM 분류 ORDER BY 분류번호').fetchall()
    return render_template('search.html', articles=articles, query=query, categories=categories)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

if __name__ == '__main__':
    app.run(debug=True)
