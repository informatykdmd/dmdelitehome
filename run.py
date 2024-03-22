from flask import Flask, render_template, redirect, url_for, flash, jsonify, session, request, current_app
from flask_wtf import FlaskForm
from flask_paginate import Pagination, get_page_args
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import mysqlDB as msq
import secrets
from datetime import datetime
from googletrans import Translator

app = Flask(__name__)
app.config['PER_PAGE'] = 6  # Określa liczbę elementów na stronie
app.config['SECRET_KEY'] = secrets.token_hex(16)

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

def getLangText(text):
    """Funkcja do tłumaczenia tekstu z polskiego na angielski"""
    translator = Translator()
    translation = translator.translate(str(text), dest='en')
    return translation.text

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

def generator_teamDB():
    took_teamD = take_data_table('*', 'workers_team')
    teamData = []
    for data in took_teamD:
        theme = {
            'ID': int(data[0]),
            'EMPLOYEE_PHOTO': data[1],
            'EMPLOYEE_NAME': data[2],
            'EMPLOYEE_ROLE': data[3],
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

def generator_daneDBList3EN(lang='en'):
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

    if session['lang'] == 'pl':
        team_list = generator_teamDB()
        fourListTeam = []
        for i, member in enumerate(team_list):
            if  i < 4: fourListTeam.append(member)
        
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)

        return render_template(
            'index-pl.html', 
            fourListTeam=fourListTeam, 
            blog_post_three=blog_post_three
            )

    if session['lang'] == 'en':
        return render_template('index-en.html')

@app.route('/done-pl')
def done():
    session['page'] = 'done'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'done-pl.html',
              blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('done-en.html')

"""
    Dune House
    Dom Kurtyna
    Circle Wood
    Wind House
    Willa Floryda
    Dom Lustrzany
    Willa Miejska
    Dom Z Gontów i Gabionów
    Lesznowolska

"""

@app.route('/dune-pl')
def dune():
    session['page'] = 'dune'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'dune-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('dune-en.html')

@app.route('/kurtyna-pl')
def kurtyna():
    session['page'] = 'kurtyna'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'kurtyna-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('kurtyna-en.html')

@app.route('/circle-pl')
def circle():
    session['page'] = 'circle'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'circle-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('circle-en.html')

@app.route('/wind-pl')
def wind():
    session['page'] = 'wind'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'wind-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('wind-en.html')

@app.route('/floryda-pl')
def floryda():
    session['page'] = 'floryda'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'floryda-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('floryda-en.html')

@app.route('/lustrzany-pl')
def lustrzany():
    session['page'] = 'lustrzany'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'lustrzany-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('lustrzany-en.html')

@app.route('/miejska-pl')
def miejska():
    session['page'] = 'miejska'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'miejska-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('miejska-en.html')

@app.route('/gonty-pl')
def gonty():
    session['page'] = 'gonty'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'gonty-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('gonty-en.html')

@app.route('/lesznowolska-pl')
def lesznowolska():
    session['page'] = 'lesznowolska'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'lesznowolska-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('lesznowolska-en.html')

@app.route('/about-pl')
def about():
    session['page'] = 'about'

    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'about-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('about-en.html')

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

    if session['lang'] == 'pl':
        team_list = generator_teamDB()
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'team-pl.html', 
            team_list=team_list, 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('team-en.html')

@app.route('/blog-full-pl')
def blogFull():
    session['page'] = 'blogFull'

    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
    
    if session['lang'] == 'en':
        blog_post = generator_daneDBList('en')
        blog_post3EN = generator_daneDBList3EN()
        blog_post_three = []
        for i, member in enumerate(blog_post3EN):
            if  i < 3: blog_post_three.append(member)

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(blog_post)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    posts = blog_post[offset: offset + per_page]

    return render_template(
            'blog-full-pl.html',
            posts=posts, 
            pagination=pagination,
            blog_post_three=blog_post_three)

@app.route('/blog-one-pl', methods=['GET'])
def blogOne():
    session['page'] = 'blogOne'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        choiced = generator_daneDBList_one_post_id(post_id_int, 'pl')
    
    if session['lang'] == 'en':
        # blog_post = generator_daneDBList('en')
        choiced = generator_daneDBList_one_post_id(post_id_int, 'en')

    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    post_id = request.args.get('post')
    try: post_id_int = int(post_id)
    except ValueError: return redirect(url_for('indexPl'))
    
    # choiced = {}
    # for one_post in blog_post:
    #     if int(one_post['id']) == post_id_int:
    #         choiced = one_post
    choiced['len'] = len(choiced['comments'])
    if session['lang'] == 'pl':
        return render_template(
            'blog-one-pl.html', 
            blog_post_three=blog_post_three,
            choiced=choiced)
    
    if session['lang'] == 'en':
        return render_template(
            'blog-one-en.html', 
            blog_post_three=blog_post_three,
            choiced=choiced)
    

@app.route('/privacy-pl')
def privacy():
    session['page'] = 'privacy'
    
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'privacy-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('privacy-en.html')

    
@app.route('/rulez-pl')
def rulez():
    session['page'] = 'rulez'

    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'ruzlez-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('ruzlez-en.html')

@app.route('/faq-pl')
def faq():
    session['page'] = 'faq'
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'faq-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('faq-en.html')

@app.route('/help-pl')
def help():
    session['page'] = 'help'

    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'help-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        blog_post = generator_daneDBList3EN()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)

        return render_template(
            'help-en.html',
            blog_post_three=blog_post_three)

@app.route('/contact-pl')
def contact():
    session['page'] = 'contact'
    
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 3: blog_post_three.append(member)
        return render_template(
            'contact-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('contact-en.html')

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
    if request.method == 'POST':
        form_data = request.json
        CLIENT_NAME = form_data['name']
        CLIENT_SUBJECT = form_data['subject']
        CLIENT_EMAIL = form_data['email']
        CLIENT_MESSAGE = form_data['message']

        # print(form_data)

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

        zapytanie_sql = '''
                INSERT INTO contact 
                    (CLIENT_NAME, CLIENT_EMAIL, SUBJECT, MESSAGE, DONE) 
                    VALUES (%s, %s, %s, %s, %s);
                '''
        dane = (CLIENT_NAME, CLIENT_EMAIL, CLIENT_SUBJECT, CLIENT_MESSAGE, 1)
        if msq.insert_to_database(zapytanie_sql, dane):
            return jsonify({'success': True, 'message': f'Wiadomość została wysłana!'})
        else:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Wystąpił problem z wysłaniem Twojej wiadomości, skontaktuj się w inny sposób lub spróbuj później!'
                })
    return redirect(url_for('indexPl'))

@app.route('/add-comm-pl', methods=['POST'])
def addComm():
    subsList = generator_subsDataDB() # pobieranie danych subskrybentów

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
                return jsonify({'success': True, 'message': f'Post został skomentowany!'})
        else:
            return jsonify({'success': False, 'message': f'Musisz być naszym subskrybentem żeby komentować naszego bloga!'})
        
    return redirect(url_for('indexPl'))

@app.route('/add-subs-pl', methods=['POST'])
def addSubs():
    subsList = generator_subsDataDB() # pobieranie danych subskrybentów
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
            zapytanie_sql = '''
                    INSERT INTO newsletter 
                        (CLIENT_NAME, CLIENT_EMAIL, ACTIVE, USER_HASH) 
                        VALUES (%s, %s, %s, %s);
                    '''
            dane = (SUB_NAME, SUB_EMAIL, 0, USER_HASH)
            if msq.insert_to_database(zapytanie_sql, dane):
                return jsonify(
                    {
                        'success': True, 
                        'message': f'Zgłoszenie nowego subskrybenta zostało wysłane, aktywuj przez email!'
                    })
        else:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Podany adres email jest już zarejestrowany!'
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
        else:
            return redirect(url_for(f'{session["page"]}'))

@app.errorhandler(404)
def page_not_found(e):
    # Tutaj możesz przekierować do dowolnej trasy, którą chcesz wyświetlić jako stronę błędu 404.
    return redirect(url_for(f'indexPl'))

if __name__ == '__main__':
    # app.run(debug=True, port=3500)
    app.run(debug=True, host='0.0.0.0', port=3500)