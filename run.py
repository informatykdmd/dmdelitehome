from flask import Flask, render_template, redirect, url_for, flash, jsonify, session, request, current_app
from flask_wtf import FlaskForm
from flask_paginate import Pagination, get_page_args
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import mysqlDB as msq
import secrets

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
        allSubsComments = take_data_where_ID('*', 'comments', 'AUTHOR_OF_COMMENT_ID', ID)
        commentsCollector = {}
        for i, com in enumerate(allSubsComments, start=1):
            commentsCollector[i] = {}
            commentsCollector[i]['id'] = com[0]
            commentsCollector[i]['message'] = com[2]
            BLOG_POST_ID = int(com[1])
            commentsCollector[i]['post_title'] = take_data_where_ID('TITLE', 'contents', 'ID', BLOG_POST_ID)[0][0]
            commentsCollector[i]['data-time'] = com[4]

        theme = {
            'id': ID, 
            'email':data[2],
            'name':data[1], 
            'status': str(data[4]), 
            'comments': commentsCollector
            }
        subsData.append(theme)
    return subsData

def generator_daneDBList():
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC;') # take_data_table('*', 'blog_posts')
    for post in took_allPost:
        id = post[0]
        id_content = post[1]
        id_author = post[2]
        post_data = post[3]

        allPostComments = take_data_where_ID('*', 'comments', 'BLOG_POST_ID', id)
        comments_dict = {}
        for i, com in enumerate(allPostComments):
            comments_dict[i] = {}
            comments_dict[i]['id'] = com[0]
            comments_dict[i]['message'] = com[2]
            comments_dict[i]['user'] = take_data_where_ID('CLIENT_NAME', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['e-mail'] = take_data_where_ID('CLIENT_EMAIL', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['data-time'] = com[4]
            
        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0],
            'introduction': take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0],
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0],
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            'contentFoto': take_data_where_ID('CONTENT_FOTO', 'contents', 'ID', id_content)[0][0],
            'additionalList': take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0],
            'tags': take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0],
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0],
            'data': take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0],
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],
            'comments': comments_dict
        }
        daneList.append(theme)
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
            if  i < 4: blog_post_three.append(member)

        return render_template(
            'index-pl.html', 
            fourListTeam=fourListTeam, 
            blog_post_three=blog_post_three
            )

    if session['lang'] == 'en':
        return render_template('index-en.html')

@app.route('/done-pl')
def done():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
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
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'dune-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('dune-en.html')

@app.route('/kurtyna-pl')
def kurtyna():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'kurtyna-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('kurtyna-en.html')

@app.route('/circle-pl')
def circle():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'circle-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('circle-en.html')

@app.route('/wind-pl')
def wind():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'wind-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('wind-en.html')

@app.route('/floryda-pl')
def floryda():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'floryda-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('floryda-en.html')

@app.route('/lustrzany-pl')
def lustrzany():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'lustrzany-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('lustrzany-en.html')

@app.route('/miejska-pl')
def miejska():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'miejska-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('miejska-en.html')

@app.route('/gonty-pl')
def gonty():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'gonty-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('gonty-en.html')

@app.route('/lesznowolska-pl')
def lesznowolska():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'lesznowolska-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('lesznowolska-en.html')

@app.route('/about-pl')
def about():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
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
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        team_list = generator_teamDB()
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'team-pl.html', 
            team_list=team_list, 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('team-en.html')

@app.route('/blog-full-pl')
def blogFull():
    blog_post = generator_daneDBList()
    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 4: blog_post_three.append(member)
    return render_template(
            'blog-full-pl.html', 
            blog_post_three=blog_post_three)

@app.route('/blog-one-pl')
def blogOne():
    blog_post = generator_daneDBList()
    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 4: blog_post_three.append(member)
    return render_template(
            'blog-one-pl.html', 
            blog_post_three=blog_post_three)

@app.route('/privacy-pl')
def privacy():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
        return render_template(
            'privacy-pl.html', 
            blog_post_three=blog_post_three)
    
    if session['lang'] == 'en':
        return render_template('privacy-en.html')

@app.route('/contact-pl')
def contact():
    if 'lang' not in session:
        session['lang'] = 'pl'

    if session['lang'] == 'pl':
        blog_post = generator_daneDBList()
        blog_post_three = []
        for i, member in enumerate(blog_post):
            if  i < 4: blog_post_three.append(member)
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


@app.route('/send-mess-pl')
def sendMess():
    return redirect(url_for('indexPl'))

@app.route('/add-comm-pl')
def addComm():
    return redirect(url_for('indexPl'))

@app.route('/add-subs-pl')
def addSubs():
    return redirect(url_for('indexPl'))

@app.route('/pl')
def langPl():
    session['lang'] = 'pl'
    return redirect(url_for('indexPl'))

@app.route('/en')
def langEn():
    session['lang'] = 'en'
    return redirect(url_for('indexPl'))

@app.errorhandler(404)
def page_not_found(e):
    # Tutaj możesz przekierować do dowolnej trasy, którą chcesz wyświetlić jako stronę błędu 404.
    return redirect(url_for('indexPl'))

if __name__ == '__main__':
    # app.run(debug=True, port=3300)
    app.run(debug=True, host='0.0.0.0', port=3500)