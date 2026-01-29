from flask import Flask, render_template, redirect, url_for, flash, jsonify, session, request, current_app, g

from flask_session import Session
from flask_paginate import Pagination, get_page_args

import mysqlDB as msq
import secrets
from datetime import datetime

import logging
from MySQLModel import MySQLModel
from typing import Optional, Union
import requests

app = Flask(__name__)
app.config['PER_PAGE'] = 6  # Określa liczbę elementów na stronie
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'  # Możesz wybrać inny backend, np. 'redis', 'sqlalchemy', itp.
Session(app)

###############################
###    ######    ######     ###
###    ######    ######     ###
###      ####    ####       ###
###      ####    ####       ###
###        ###  ###         ###
###         ######          ###
###        ######           ###
###      ###    ###         ###
###     ####     ####       ###
###     ####     ####       ###
###    ######    ######     ###
###    ######    ######     ###
###############################

# Instancja MySql
def get_db():
    if 'db' not in g:
        g.db = MySQLModel(permanent_connection=False)
    return g.db

def getLangText(text, dest="en", source="pl"):
    if not text:
        return text
    # bezpiecznik: nie tłumacz "ścian"
    if len(text) > 8000:
        return text
    try:
        r = requests.post(
            "http://127.0.0.1:5055/translate",
            json={"text": text, "source": source, "target": dest, "format": "text"},
            timeout=(2, 8),
        )
        r.raise_for_status()
        return r.json().get("text", text)
    except Exception as e:
        print(f"Exception Error: {e}")
        return text

# def getLangText_mistral(text):
#     """Funkcja do tłumaczenia tekstu z polskiego na angielski"""
#     mgr = MistralChatManager(MISTRAL_API_KEY)
#     out = mgr.translate(text, target_lang='en')
#     return out

def getLangText_old(text):
    """Funkcja do tłumaczenia tekstu z polskiego na angielski"""
    # from googletrans import Translator
    # translator = Translator()
    # translation = translator.translate(str(text), dest='en')
    # return translation.text

def format_date(date_input, pl=True):
    ang_pol = {
        'January': 'styczeń',
        'February': 'luty',
        'March': 'marzec',
        'April': 'kwiecień',
        'May': 'maj',
        'June': 'czerwiec',
        'July': 'lipiec',
        'August': 'sierpień',
        'September': 'wrzesień',
        'October': 'październik',
        'November': 'listopad',
        'December': 'grudzień'
    }
    # Sprawdzenie czy data_input jest instancją stringa; jeśli nie, zakładamy, że to datetime
    if isinstance(date_input, str):
        date_object = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
    else:
        # Jeśli date_input jest już obiektem datetime, używamy go bezpośrednio
        date_object = date_input

    formatted_date = date_object.strftime('%d %B %Y')
    if pl:
        for en, pl in ang_pol.items():
            formatted_date = formatted_date.replace(en, pl)

    return formatted_date

#  Funkcja pobiera dane z bazy danych 
def take_data_where_ID(key, table, id_name, ID):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID};')
    return dump_key

def take_data_table(key, table):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table};')
    return dump_key

def generator_teamDB(lang='pl'):
    took_teamD = take_data_table('*', 'workers_team')
    teamData = []
    for data in took_teamD:
        theme = {
            'ID': int(data[0]),
            'EMPLOYEE_PHOTO': data[1],
            'EMPLOYEE_NAME': data[2],
            'EMPLOYEE_ROLE': data[3] if lang=='pl' else getLangText(data[3]),
            'EMPLOYEE_DEPARTMENT': data[4],
            'PHONE':'' if data[5] is None else data[5],
            'EMAIL': '' if data[6] is None else data[6],
            'FACEBOOK': '' if data[7] is None else data[7],
            'LINKEDIN': '' if data[8] is None else data[8],
            'DATE_TIME': data[9],
            'STATUS': int(data[10])
        }
        # dostosowane dla elitehome
        if data[4] == 'dmd elitehome':
            teamData.append(theme)
    return teamData

def generator_subsDataDB():
    subsData = []
    took_subsD = take_data_table('*', 'newsletter')
    for data in took_subsD:
        if data[4] != 1: continue
        ID = data[0]
        theme = {
            'id': ID, 
            'email':data[2],
            'name':data[1], 
            'status': str(data[4]), 
            }
        subsData.append(theme)
    return subsData

def generator_daneDBList(lang='pl'):
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC;') # take_data_table('*', 'blog_posts')
    for post in took_allPost:
        id = post[0]
        id_content = post[1]
        id_author = post[2]

        allPostComments = take_data_where_ID('*', 'comments', 'BLOG_POST_ID', id)
        comments_dict = {}
        for i, com in enumerate(allPostComments):
            comments_dict[i] = {}
            comments_dict[i]['id'] = com[0]
            comments_dict[i]['message'] = com[2] if lang=='pl' else getLangText(com[2])
            comments_dict[i]['user'] = take_data_where_ID('CLIENT_NAME', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['e-mail'] = take_data_where_ID('CLIENT_EMAIL', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['avatar'] = take_data_where_ID('AVATAR_USER', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['data-time'] = format_date(com[4]) if lang=='pl' else format_date(com[4], False)
            
        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            'introduction': take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0]),
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0]),
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            'contentFoto': take_data_where_ID('CONTENT_FOTO', 'contents', 'ID', id_content)[0][0],
            'additionalList': str(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0]).split('#splx#') if lang=='pl' else str(getLangText(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0])).replace('#SPLX#', '#splx#').split('#splx#'),
            'tags': str(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0]).split(', ') if lang=='pl' else str(getLangText(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0])).split(', '),
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0]) if lang=='pl' else format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

            'author_about': take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0] if lang=='pl' else getLangText(take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0]),
            'author_avatar': take_data_where_ID('AVATAR_AUTHOR', 'authors', 'ID', id_author)[0][0],
            'author_facebook': take_data_where_ID('FACEBOOK', 'authors', 'ID', id_author)[0][0],
            'author_twitter': take_data_where_ID('TWITER_X', 'authors', 'ID', id_author)[0][0],
            'author_instagram': take_data_where_ID('INSTAGRAM', 'authors', 'ID', id_author)[0][0],

            'comments': comments_dict
        }
        daneList.append(theme)
    return daneList

def generator_daneDBList_short(lang='pl'):
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts WHERE DATE_TIME >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH) ORDER BY ID DESC;') # take_data_table('*', 'blog_posts')
    for post in took_allPost:

        id_content = post[1]
        id_author = post[2]

        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0]),
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0]) if lang=='pl' else format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

        }
        daneList.append(theme)
    return daneList

def generator_daneDBList_one_post_id(id_post, lang='pl'):
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts WHERE ID={id_post};') # take_data_table('*', 'blog_posts')
    for post in took_allPost:
        id = post[0]
        id_content = post[1]
        id_author = post[2]

        allPostComments = take_data_where_ID('*', 'comments', 'BLOG_POST_ID', id)
        comments_dict = {}
        for i, com in enumerate(allPostComments):
            comments_dict[i] = {}
            comments_dict[i]['id'] = com[0]
            comments_dict[i]['message'] = com[2] if lang=='pl' else getLangText(com[2])
            comments_dict[i]['user'] = take_data_where_ID('CLIENT_NAME', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['e-mail'] = take_data_where_ID('CLIENT_EMAIL', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['avatar'] = take_data_where_ID('AVATAR_USER', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['data-time'] = format_date(com[4]) if lang=='pl' else format_date(com[4], False)
            
        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            'introduction': take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0]),
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0]),
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            'contentFoto': take_data_where_ID('CONTENT_FOTO', 'contents', 'ID', id_content)[0][0],
            'additionalList': str(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0]).split('#splx#') if lang=='pl' else str(getLangText(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0])).replace('#SPLX#', '#splx#').split('#splx#'),
            'tags': str(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0]).split(', ') if lang=='pl' else str(getLangText(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0])).split(', '),
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0]) if lang=='pl' else format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

            'author_about': take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0] if lang=='pl' else getLangText(take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0]),
            'author_avatar': take_data_where_ID('AVATAR_AUTHOR', 'authors', 'ID', id_author)[0][0],
            'author_facebook': take_data_where_ID('FACEBOOK', 'authors', 'ID', id_author)[0][0],
            'author_twitter': take_data_where_ID('TWITER_X', 'authors', 'ID', id_author)[0][0],
            'author_instagram': take_data_where_ID('INSTAGRAM', 'authors', 'ID', id_author)[0][0],

            'comments': comments_dict
        }
        daneList.append(theme)
    return daneList

def generator_daneDBList_3(lang='en'):
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC;') # take_data_table('*', 'blog_posts')
    for i, post in enumerate(took_allPost):
        id_content = post[1]
        id_author = post[2]

        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

        }
        daneList.append(theme)
        if i == 2:
            break
    return daneList

def mainDataGeneratorDict():
    data = {
        "BLOG-ALLPOSTS-PL": generator_daneDBList('pl'),
        "BLOG-ALLPOSTS-EN": generator_daneDBList('en'),
        "BLOG-SHORT-PL": generator_daneDBList_short('pl'),
        "BLOG-SHORT-EN": generator_daneDBList_short('en'),
        "BLOG-FOOTER-PL": generator_daneDBList_3('pl'),
        "BLOG-FOOTER-EN": generator_daneDBList_3('en'),
        "TEAM-ALL-PL": generator_teamDB('pl'),
        "TEAM-ALL-EN": generator_teamDB('en'),
        "SUBS-ALL-PL": generator_subsDataDB()
    }
    return data

def getProjectData(project_id: int, lang: str = "pl"):
    """
    Czyta rekord z realizacje_elitehome i buduje słownik 'theme'.
    fetch_one ustawia atrybuty na obiekcie db, więc odczyt robimy przez getattr(db, "<kolumna>", None).
    """
    db = get_db()  # musi zwrócić instancję MySQLModel (albo stwórz: MySQLModel(permanent_connection=True))
    query = """
        SELECT *
        FROM realizacje_elitehome
        WHERE id = %s
        LIMIT 1;
    """
    params = (project_id,)
    db.fetch_one(query, params=params)  # ustawi atrybuty na db (np. db.id, db.tytul, db.opis_1, ...)

    # Jeśli nie znaleziono rekordu, kolumna 'id' pozostanie None (po _fetch_columns); zwróć None
    if getattr(db, "id", None) is None:
        return None

    def col(k, default=None):
        return getattr(db, k, default)

    def tr(val):
        if val in (None, ""):
            return val
        # polski -> bez zmian; inne -> przepuść przez getLangText
        return val if lang == "pl" else getLangText(val)

    theme = {
        "id": col("id"),

        "tytul": tr(col("tytul")),
        "r_start": col("r_start"),
        "r_finish": col("r_finish"),

        "slogan_1": tr(col("slogan_1")),
        "slogan_2": tr(col("slogan_2")),
        "slogan_3": tr(col("slogan_3")),
        "slogan_4": tr(col("slogan_4")),

        "tytul_1": tr(col("tytul_1")),
        "podtytul_1": tr(col("podtytul_1")),
        "opis_1": tr(col("opis_1")),

        "tytul_2": tr(col("tytul_2")),
        "podtytul_2": tr(col("podtytul_2")),
        "opis_2": tr(col("opis_2")),

        "tytul_zagadek": tr(col("tytul_zagadek")),
        "podtytul_zagadek": tr(col("podtytul_zagadek")),
        "zagadka_1_tytul": tr(col("zagadka_1_tytul")),
        "zagadka_1_opis": tr(col("zagadka_1_opis")),
        "zagadka_2_tytul": tr(col("zagadka_2_tytul")),
        "zagadka_2_opis": tr(col("zagadka_2_opis")),
        "zagadka_3_tytul": tr(col("zagadka_3_tytul")),
        "zagadka_3_opis": tr(col("zagadka_3_opis")),

        "minaturka": col("minaturka"),
        "paralax_1": col("paralax_1"),
        "paralax_2": col("paralax_2"),
        "inside_1": col("inside_1"),
        "inside_2": col("inside_2"),

        "data_aktualizacji": col("data_aktualizacji")
    }

    return theme


def get_realizacje_overview(
        exclude_id: Optional[Union[int, str]] = None, lang: str = "pl"):
    """
    Zwraca:
    {
      "list": [ { "id", "tytul", "link", "r_start", "r_finish", "minaturka" }, ... ],
      "shortcuts": [  # 1 skrót na każde 5 realizacji
         { "minaturka", "label", "link" },
         ...
      ],
      "count": <liczba pozycji po odfiltrowaniu>
    }
    """
    db = get_db()  # instancja MySQLModel
    rows = db.getFrom(
        """
        SELECT id, tytul, minaturka, r_start, r_finish
        FROM realizacje_elitehome
        ORDER BY COALESCE(r_start, 0) DESC, id DESC
        """,
        as_dict=True
    )

    # --- exclude_id: pojedynczy int lub str(int)
    ex_id: Optional[int] = None
    if exclude_id is not None:
        try:
            ex_id = int(exclude_id)
        except (TypeError, ValueError):
            ex_id = None  # jeśli nie uda się sparsować, traktuj jak brak wykluczenia

    def tr(val):
        if val in (None, ""):
            return val
        return val if lang == "pl" else getLangText(val)

    def fmt_period(start: Optional[int], finish: Optional[int]) -> str:
        if isinstance(start, int) and isinstance(finish, int):
            return f"{start} - {finish}"
        if isinstance(start, int) and finish is None:
            return f"od {start}"
        if start is None and isinstance(finish, int):
            return f"do {finish}"
        return ""

    # --- pełna lista (po filtrze exclude_id)
    items = []
    for r in rows:
        if ex_id is not None and r["id"] == ex_id:
            continue
        link = f"/realizacje?id={r['id']}"
        items.append({
            "id": r["id"],
            "tytul": tr(r["tytul"]),
            "link": link,
            "r_start": r["r_start"],   # int lub None
            "r_finish": r["r_finish"], # int lub None
            "minaturka": r["minaturka"],
        })

    # --- skróty: 1 skrót na każde 5 realizacji → bierzemy pierwszą z każdej piątki
    shortcuts = []
    for i in range(0, len(items), 4):
        group = items[i:i+4]
        if not group:
            continue
        first = group[0]  # reprezentant piątki (jeśli wolisz ostatnią: group[-1])
        label = f"{first['tytul']} {fmt_period(first['r_start'], first['r_finish'])}".strip()
        scope = f"{fmt_period(first['r_start'], first['r_finish'])}".strip()
        shortcuts.append({
            "minaturka": first["minaturka"],
            "label": label,
            "title": first['tytul'],
            "scope": scope,
            "link": first["link"],
        })

    return {
        "list": items,
        "shortcuts": shortcuts,
        "count": len(items),
    }


logFileName = '/home/johndoe/app/dmdelitehome/logs/access.log'  # 🔁 ZMIENIAJ dla każdej aplikacji

# Konfiguracja loggera
logging.basicConfig(filename=logFileName, level=logging.INFO,
                    format='%(asctime)s - %(message)s', filemode='a')

# Funkcja do logowania informacji o zapytaniu
def log_request():
    ip_address = request.remote_addr
    date_time = datetime.now()
    endpoint = request.endpoint or request.path  # fallback jeśli brak endpointu
    method = request.method

    logging.info(f'IP: {ip_address}, Time: {date_time}, Endpoint: {endpoint}, Method: {method}')

@app.before_request
def before_request_logging():
    log_request()

############################
##      ######           ###
##      ######           ###
##     ####              ###
##     ####              ###
##    ####               ###
##    ####               ###
##   ####                ###
##   ####                ###
#####                    ###
#####                    ###
##   ####                ###
##   ####                ###
##    ####               ###
##    ####               ###
##     ####              ###
##     ####              ###
##      ######           ###
##      ######           ###
############################

@app.route('/')
def indexPl():
    session['page'] = 'indexPl'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if f'TEAM-ALL-{session["lang"]}' not in session:
        team_list = generator_teamDB(session["lang"])
        session[f'TEAM-ALL-{session["lang"]}'] = team_list
    else:
        team_list = session[f'TEAM-ALL-{session["lang"]}']

    fourListTeam = []
    for i, member in enumerate(team_list):
        if  i < 4: fourListTeam.append(member)
        
    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']
    
    other_projects = get_realizacje_overview(None, session['lang'])
    
    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
        f'index-{session["lang"]}.html', 
        fourListTeam=fourListTeam, 
        blog_post_three=blog_post_three,
        other_projects=other_projects
        )

    

@app.route('/done-pl')
def done():
    session['page'] = 'done'
    if 'lang' not in session:
        session['lang'] = 'pl'
    
    other_projects = get_realizacje_overview(None, session['lang'])

    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']

    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
        f'done-{session["lang"]}.html', 
        blog_post_three=blog_post_three,
        other_projects=other_projects
        )
    


@app.route('/realizacje', methods=['GET'])
def realizacje():
    session['page'] = 'realizacje'

    if 'id' in request.args:
        project_id = request.args.get('id')
    else:
        return redirect(url_for(f'indexPl'))
    
    if 'lang' not in session:
        session['lang'] = 'pl'
    
    pro_data = getProjectData(project_id, session['lang'])
    other_projects = get_realizacje_overview(project_id, session['lang'])
    
    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']

    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
        f'projects-{session["lang"]}.html', 
        blog_post_three=blog_post_three,
        pro_data=pro_data,
        other_projects=other_projects
        )


@app.route('/about-pl')
def about():
    session['page'] = 'about'

    if 'lang' not in session:
        session['lang'] = 'pl'

    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']

    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
        f'about-{session["lang"]}.html', 
        blog_post_three=blog_post_three)

############################
###      ##########      ###
###      ##########      ###
###     ###      ###     ###
###     ###      ###     ###
###    ###        ###    ###
###    ###        ###    ###
###    ###        ###    ###
###    ###        ###    ###
###     ###      ###     ###
###     ###      ###     ###
###      ##########      ###
###      ##########      ###
############################

@app.route('/team-pl')
def team():
    session['page'] = 'team'

    if 'lang' not in session:
        session['lang'] = 'pl'

    if f'TEAM-ALL-{session["lang"]}' not in session:
        team_list = generator_teamDB(session["lang"])
        session[f'TEAM-ALL-{session["lang"]}'] = team_list
    else:
        team_list = session[f'TEAM-ALL-{session["lang"]}']

    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']

    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)
    return render_template(
        f'team-{session["lang"]}.html', 
        team_list=team_list, 
        blog_post_three=blog_post_three)
    


@app.route('/blog-full-pl')
def blogFull():
    session['page'] = 'blogFull'

    if 'lang' not in session:
        session['lang'] = 'pl'

    if f'BLOG-SHORT-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_short(session["lang"])
        session[f'BLOG-SHORT-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-SHORT-{session["lang"]}']

    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post_3 = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post_3
    else:
        blog_post_3 = session[f'BLOG-FOOTER-{session["lang"]}']

    blog_post_three = []
    for i, member in enumerate(blog_post_3):
        if  i < 3: blog_post_three.append(member)

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(blog_post)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    posts = blog_post[offset: offset + per_page]

    return render_template(
            f'blog-full-{session["lang"]}.html', 
            posts=posts, 
            pagination=pagination,
            blog_post_three=blog_post_three)

@app.route('/blog-one-pl', methods=['GET'])
def blogOne():
    session['page'] = 'blogOne'
    if 'post' in request.args:
        post_id = request.args.get('post')
        try: post_id_int = int(post_id)
        except ValueError: return redirect(url_for('indexPl'))
    else:
        return redirect(url_for(f'indexPl'))

    if 'lang' not in session:
        session['lang'] = 'pl'

    
    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']

    choiced = generator_daneDBList_one_post_id(post_id_int, session["lang"])[0]
    
    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    choiced['len'] = len(choiced['comments'])

    return render_template(
        f'blog-one-{session["lang"]}.html', 
        blog_post_three=blog_post_three,
        choiced=choiced)
    
   
    

@app.route('/privacy-pl')
def privacy():
    session['page'] = 'privacy'
    
    if 'lang' not in session:
        session['lang'] = 'pl'

    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']

    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
            f'privacy-{session["lang"]}.html',
            blog_post_three=blog_post_three)


    
@app.route('/rulez-pl')
def rulez():
    session['page'] = 'rulez'

    if 'lang' not in session:
        session['lang'] = 'pl'

    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']
    
    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
            f'ruzlez-{session["lang"]}.html',
            blog_post_three=blog_post_three)


@app.route('/faq-pl')
def faq():
    session['page'] = 'faq'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']

    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
            f'faq-{session["lang"]}.html',
            blog_post_three=blog_post_three)


@app.route('/help-pl')
def help():
    session['page'] = 'help'

    if 'lang' not in session:
        session['lang'] = 'pl'

    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']

    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
            f'help-{session["lang"]}.html',
            blog_post_three=blog_post_three)

@app.route('/contact-pl')
def contact():
    session['page'] = 'contact'
    
    if 'lang' not in session:
        session['lang'] = 'pl'

    if f'BLOG-FOOTER-{session["lang"]}' not in session:
        blog_post = generator_daneDBList_3(session["lang"])
        session[f'BLOG-FOOTER-{session["lang"]}'] = blog_post
    else:
        blog_post = session[f'BLOG-FOOTER-{session["lang"]}']


    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)
    
    return render_template(
        f'contact-{session["lang"]}.html', 
        blog_post_three=blog_post_three)
    
   

############################
###                      ###
###                      ###
###                      ###
###                      ###
###                      ###
###                      ###
###                      ###
###                      ###
###      ##############  ###
###      ##############  ###
############################


@app.route('/send-mess-pl', methods=['POST'])
def sendMess():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if request.method == 'POST':
        form_data = request.json
        CLIENT_NAME = form_data['name']
        CLIENT_SUBJECT = form_data['subject']
        CLIENT_EMAIL = form_data['email']
        CLIENT_MESSAGE = form_data['message']

        if session["lang"] == 'pl':
            if 'condition' not in form_data:
                return jsonify(
                    {
                        'success': False, 
                        'message': f'Musisz zaakceptować naszą politykę prywatności!'
                    })
            if CLIENT_NAME == '':
                return jsonify(
                    {
                        'success': False, 
                        'message': f'Musisz podać swoje Imię i Nazwisko!'
                    })
            if CLIENT_SUBJECT == '':
                return jsonify(
                    {
                        'success': False, 
                        'message': f'Musisz podać temat wiadomości!'
                    })
            if CLIENT_EMAIL == '' or '@' not in CLIENT_EMAIL or '.' not in CLIENT_EMAIL or len(CLIENT_EMAIL) < 7:
                return jsonify(
                    {
                        'success': False, 
                        'message': f'Musisz podać adres email!'
                    })
            if CLIENT_MESSAGE == '':
                return jsonify(
                    {
                        'success': False, 
                        'message': f'Musisz podać treść wiadomości!'
                    })
        if session["lang"] == 'en':
            if 'condition' not in form_data:
                return jsonify(
                    {
                        'success': False, 
                        'message': f'You must accept our privacy policy!'
                    })
            if CLIENT_NAME == '':
                return jsonify(
                    {
                        'success': False, 
                        'message': f'You must provide your Full Name!'
                    })
            if CLIENT_SUBJECT == '':
                return jsonify(
                    {
                        'success': False, 
                        'message': f'You must provide the subject of the message!'
                    })
            if CLIENT_EMAIL == '' or '@' not in CLIENT_EMAIL or '.' not in CLIENT_EMAIL or len(CLIENT_EMAIL) < 7:
                return jsonify(
                    {
                        'success': False, 
                        'message': f'You must provide a valid email address!'
                    })
            if CLIENT_MESSAGE == '':
                return jsonify(
                    {
                        'success': False, 
                        'message': f'You must provide the message content!'
                    })


        # --- meta z żądania (Flask/FastAPI) ---
        ref = request.headers.get('Referer')
        ua  = request.headers.get('User-Agent')
        # Host: w Flask jest też request.host; w FastAPI/Starlette z ASGI bywa tylko nagłówek
        host = request.headers.get('Host') or getattr(request, 'host', None)

        # Realne IP z uwzględnieniem proxy/CDN:
        xff = request.headers.get('X-Forwarded-For', '')
        ip_from_xff = xff.split(',')[0].strip() if xff else None
        ip = (request.headers.get('CF-Connecting-IP') or ip_from_xff or request.remote_addr)

        zapytanie_sql = '''
            INSERT INTO contact 
                (CLIENT_NAME, CLIENT_EMAIL, SUBJECT, MESSAGE, DONE, remote_ip, referer, user_agent, source_host) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''
        dane = (
            CLIENT_NAME,
            CLIENT_EMAIL,
            CLIENT_SUBJECT,
            CLIENT_MESSAGE,
            1,
            ip,
            ref,
            ua,
            host
        )
        if msq.insert_to_database(zapytanie_sql, dane):
            if session["lang"] == "pl":
                return jsonify({'success': True, 'message': f'Wiadomość została wysłana!'})
            if  session["lang"] == "en":
                return jsonify({'success': True, 'message': f"Your message has been sent!"})
        else:
            if session["lang"] == "pl":
                return jsonify(
                    {
                        'success': False, 
                        'message': f'Wystąpił problem z wysłaniem Twojej wiadomości, skontaktuj się w inny sposób lub spróbuj później!'
                    })
            if  session["lang"] == "en":
                return jsonify(
                    {
                        'success': False, 
                        'message': f'There was a problem sending your message, please contact us in another way or try again later!'
                    })

    return redirect(url_for('indexPl'))

@app.route('/add-comm-pl', methods=['POST'])
def addComm():
    subsList = generator_subsDataDB() # pobieranie danych subskrybentów

    if 'lang' not in session:
        session['lang'] = 'pl'

    if request.method == 'POST':
        form_data = request.json
        # print(form_data)
        SUB_ID = None
        SUB_NAME = form_data['Name']
        SUB_EMAIL = form_data['Email']
        SUB_COMMENT = form_data['Comment']
        POST_ID = form_data['id']
        allowed = False
        for subscriber in subsList:
            if subscriber['email'] == SUB_EMAIL and subscriber['name'] == SUB_NAME and int(subscriber['status']) == 1:
                allowed = True
                SUB_ID = subscriber['id']
                break
        if allowed and SUB_ID:
            # print(form_data)
            zapytanie_sql = '''
                    INSERT INTO comments 
                        (BLOG_POST_ID, COMMENT_CONNTENT, AUTHOR_OF_COMMENT_ID) 
                        VALUES (%s, %s, %s);
                    '''
            dane = (POST_ID, SUB_COMMENT, SUB_ID)
            if msq.insert_to_database(zapytanie_sql, dane):
                if session["lang"] == "pl":
                    return jsonify({'success': True, 'message': f'Post został skomentowany!'})
                if session["lang"] == "en":
                    return jsonify({'success': True, 'message': f"The post has been commented!"})
        else:
            if session["lang"] == "pl":
                return jsonify({'success': False, 'message': f'Musisz być naszym subskrybentem żeby komentować naszego bloga!'})
            if session["lang"] == "en":
                return jsonify({'success': False, 'message': f'You must be our subscriber to comment on our blog!'})

        
    return redirect(url_for('indexPl'))

@app.route('/add-subs-pl', methods=['POST'])
def addSubs():
    subsList = generator_subsDataDB() # pobieranie danych subskrybentów

    if 'lang' not in session:
        session['lang'] = 'pl'

    if request.method == 'POST':
        form_data = request.json

        SUB_NAME = form_data['Imie']
        SUB_EMAIL = form_data['Email']
        USER_HASH = secrets.token_hex(20)

        allowed = True
        for subscriber in subsList:
            if subscriber['email'] == SUB_EMAIL:
                allowed = False

        if allowed:
            # --- meta z żądania (Flask/FastAPI) ---
            ref = request.headers.get('Referer')
            ua  = request.headers.get('User-Agent')
            host = request.headers.get('Host') or getattr(request, 'host', None)

            # Realne IP z uwzględnieniem proxy/CDN:
            xff = request.headers.get('X-Forwarded-For', '')
            ip_from_xff = xff.split(',')[0].strip() if xff else None
            ip = (request.headers.get('CF-Connecting-IP') or ip_from_xff or request.remote_addr)

            # (opcjonalnie) bardzo prosty anty-bot: wymagaj swojej domeny w referer + niepusty UA
            # if (not ua or not ua.strip()) or (ref and 'dmdbudownictwo.pl' not in ref):
            #     abort(403)

            zapytanie_sql = '''
                INSERT INTO newsletter 
                    (CLIENT_NAME, CLIENT_EMAIL, ACTIVE, USER_HASH, remote_ip, referer, user_agent, source_host) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            '''
            dane = (SUB_NAME, SUB_EMAIL, 0, USER_HASH, ip, ref, ua, host)
            
            if msq.insert_to_database(zapytanie_sql, dane):
                if session["lang"] == "pl":
                    return jsonify(
                        {
                            'success': True, 
                            'message': f'Zgłoszenie nowego subskrybenta zostało wysłane, aktywuj przez email!'
                        })
                if session["lang"] == "en":
                    return jsonify({"success":True,"message":"Successfully added!"})
        else:
            if session["lang"] == "pl":
                return jsonify(
                    {
                        'success': False, 
                        'message': f'Podany adres email jest już zarejestrowany!'
                    })
            if session["lang"] == "en":
                return jsonify(
                    {
                        'success': False, 
                        'message': f'The provided email address is already registered!'
                    })

    return redirect(url_for('indexPl'))


@app.route('/pl')
def langPl():

    session['lang'] = 'pl'
    if 'page' not in session:
        return redirect(url_for(f'indexPl'))
    else:
        if session['page'] == 'blogOne':
            return redirect(url_for(f'blogFull'))
        elif session['page'] == 'realizacje':
            return redirect(url_for(f'done'))
        else:
            return redirect(url_for(f'{session["page"]}'))

@app.route('/en')
def langEn():
    session['lang'] = 'en'

    if 'page' not in session:
        return redirect(url_for(f'indexPl'))
    else:
        if session['page'] == 'blogOne':
            return redirect(url_for(f'blogFull'))
        elif session['page'] == 'realizacje':
            return redirect(url_for(f'done'))
        else:
            return redirect(url_for(f'{session["page"]}'))

@app.errorhandler(404)
def page_not_found(e):
    # Tutaj możesz przekierować do dowolnej trasy, którą chcesz wyświetlić jako stronę błędu 404.
    return redirect(url_for(f'indexPl'))

if __name__ == '__main__':
    # app.run(debug=True, port=3500)
    app.run(debug=True, host='0.0.0.0', port=3500)