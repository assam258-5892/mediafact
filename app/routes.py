from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__, template_folder='../templates', static_folder='../static')
DATABASE = 'db/mediafact.db'

# DB 연결 함수
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# 메인(최신 기사 목록)
@app.route('/')
def index():
    db = get_db()
    articles = db.execute('SELECT * FROM 기사 ORDER BY 작성일자 DESC LIMIT 20').fetchall()
    return render_template('index.html', articles=articles)

# 기사 상세
@app.route('/article/<int:article_id>')
def article_detail(article_id):
    db = get_db()
    try:
        article = db.execute('SELECT * FROM 기사 WHERE 기사번호=?', (article_id,)).fetchone()
        photos = db.execute('SELECT * FROM 사진 WHERE 기사번호=?', (article_id,)).fetchall()
        reporter = db.execute('SELECT * FROM 기자 WHERE 기자번호=?', (article['기자번호'],)).fetchone() if article else None
    except Exception as e:
        article, photos, reporter = None, [], None
    return render_template('article.html', article=article, photos=photos, reporter=reporter)

# 카테고리별 기사
@app.route('/category/<int:category_id>')
def category(category_id):
    db = get_db()
    articles = db.execute('SELECT * FROM 기사 WHERE 분류번호=? ORDER BY 작성일자 DESC', (category_id,)).fetchall()
    return render_template('category.html', articles=articles)

# 기자별 기사
@app.route('/reporter/<int:reporter_id>')
def reporter(reporter_id):
    db = get_db()
    articles = db.execute('SELECT * FROM 기사 WHERE 기자번호=? ORDER BY 작성일자 DESC', (reporter_id,)).fetchall()
    reporter = db.execute('SELECT * FROM 기자 WHERE 기자번호=?', (reporter_id,)).fetchone()
    return render_template('reporter.html', articles=articles, reporter=reporter)

# 사진 갤러리
@app.route('/photo')
def photo_gallery():
    db = get_db()
    photos = db.execute('SELECT * FROM 사진 ORDER BY 등록일자 DESC').fetchall()
    return render_template('photo.html', photos=photos)

# 기사 검색(FTS5)
@app.route('/search')
def search():
    query = request.args.get('q', '')
    db = get_db()
    articles = []
    if query:
        try:
            sql = '''SELECT 기사.* FROM 기사전문색인 JOIN 기사 ON 기사전문색인.기사번호 = 기사.기사번호 WHERE 기사전문색인 MATCH ? ORDER BY 기사.작성일자 DESC'''
            articles = db.execute(sql, (query,)).fetchall()
        except Exception as e:
            articles = []
    return render_template('search.html', articles=articles, query=query)

if __name__ == '__main__':
    app.run(debug=True)
