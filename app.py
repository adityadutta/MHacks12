import pprint
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from firebase_admin import credentials
import firebase_admin
from database import DatabaseManager, Note
from flask import Flask, render_template, request, flash, redirect
import requests
import getsearch
from forms import AddNoteForm, SuperNoteForm
import os
import translation
from Google_Key_Test import NoteAnalysis

credential_path = "TranslationKey.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'

lang = "en"


app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'

if (not len(firebase_admin._apps)):
    cred = credentials.Certificate(
        'static/mhacks12-22906-firebase-adminsdk-lbt7e-d7c9a27bb5.json')
    default_app = firebase_admin.initialize_app(
        cred,  {'databaseURL': 'https://mhacks12-22906.firebaseio.com/'})
previous = ""
account_sid = '[contact billbai0102@gmail.com for twilio SID]'
auth_token = '[contact billbai0102@gmail.com for twilio private API key]'

dm = DatabaseManager("super_notes")
notesManager = DatabaseManager("notes")
sn_translated = "Oops! Something's wrong with Twilio servers!"


@app.route('/')
def main():
    return render_template('index.html')


@app.route("/index")
def index():
    data = get_supernote("Physics")
    user = "Bill"
    return render_template('index.html', data=data, user=user)


#####TWILIO######
@app.route("/sms", methods=['GET', 'POST'])
def sms_ahoy_reply():
    global lang
    global sn_translated
    courses = ["physics", "computer science"]  # WHERE THE COURSES ARE STORED
    client = Client(account_sid, auth_token)
    resp = MessagingResponse()
    premes = ""
    messages = client.messages.list(limit=1)
    for record in messages:
        premes = record.body
        print(".1.1.1.1.1.1.1")
        print(premes)
        print(".1.1.1.1.1.1.1")

    if(translation.createTranslation(premes, "English").lower() in courses):
        super_notes_list = dm.find_notes_by_course_name(
            translation.createTranslation(premes, language="en").lower())
        print("----------")
        print(lang)
        print("----------")
        for note in super_notes_list:
            sn_translated = translation.createTranslation(note['note'], lang)
            print(note['note'])
        sn_translated = sn_translated.replace('&#39;', '\'')
        resp.message(sn_translated[:1550] + ".")
        return str(resp)

    lang = str(premes)
    resp.message(translation.createTranslation(
        "Enter a course you wish to learn about.", language=lang))
    return str(resp)


def get_supernote(course):
    cl = dm.find_notes_by_course_name(course)
    return cl


@app.route("/results")
def results():
    return render_template('results.html')


@app.route('/search', methods=['POST'])
def pass_val():
    search = request.form.get('search')
    language = 'en' if request.form.get('language-choice') is " " or request.form.get('language-choice') is None else request.form.get('language-choice')
    print(language)
    print(search + language)
    s = translation.createTranslation(search, "EN")
    s = s.replace('&#39;', '\'')
    print(s)
    key = dm.get_last_super_note_key(s)
    print(key)
    super_note = dm.get_note_key(dm.get_last_super_note_key(s)) #dm.find_notes_by_course_name(s)
    pprint.pprint(super_note)

    sn_translated = translation.createTranslation(super_note['note'], language)
    sn_translated = sn_translated.replace('&#39;', '\'')
    title_translated = translation.createTranslation(
        super_note['course_name'], language)
    title_translated = title_translated.replace('&#39;', '\'')
    pprint.pprint(sn_translated)
    # sn_translated = sn_translated.replace('\n', '<br/><br/> - ')
    print(sn_translated)
    return render_template('results.html', note=sn_translated, title=title_translated, upvotes=super_note["upvotes"], key = key, note_type = "super_note")


@app.route('/add_note')
def add_note():
    form = AddNoteForm()
    return render_template('add_note.html', title='Add New Note', form=form)


@app.route('/add_note', methods=['POST'])
def add_new_note():
    form = AddNoteForm()
    if form.validate_on_submit():
        course_name = form.course_name.data
        n_translated = translation.createTranslation(form.note.data, "EN")
        n_translated = n_translated.replace('&#39;', '\'')
        new_note = Note(form.course_key.data,
                        course_name.lower(), n_translated)
        note_key = notesManager.add_note_to_db(new_note)
        flash('Note Added: With course key: {} and Course Name: {} .  Share your notes with your friends or save it for future use: {}'.format(
            form.course_key.data, form.course_name.data, note_key))
        auto_gen_super_note(course_name.lower())
        return redirect('/index')
    return render_template('add_note.html', title='Add New Note', form=form)


@app.route('/super_note', methods=['POST'])
def generate_super_note():
    form = SuperNoteForm()
    sn = ""
    if form.validate_on_submit():
        na = NoteAnalysis(form.key1.data, form.key2.data)
        sn = na.run_quickstart()
    return render_template('results.html', note=sn)


@app.route('/super_note')
def super_note():
    form = SuperNoteForm()
    return render_template('super_note.html', title='Generate Super Note', form=form)


@app.route('/search_key')
def search_key_page():
    return render_template('search_key.html')


@app.route('/search_key', methods=['POST'])
def search_key():
    key = request.form.get('key')
    language = 'en' if request.form.get('language-choice') is " " or request.form.get('language-choice') is None else request.form.get('language-choice')
    print(key + language)
    note_data = notesManager.get_note_key(key)
    pprint.pprint(note_data)
    sn_translated = translation.createTranslation(note_data["note"], language)
    pprint.pprint(sn_translated)
    return render_template('results.html', note=sn_translated, upvotes=note_data["upvotes"], key = key, note_type = "note")

def auto_gen_super_note(course_name):
    last_super_note_key = dm.get_last_super_note_key(course_name)
    last_course_note_key = notesManager.get_last_course_note_key(course_name)

    na = NoteAnalysis(last_super_note_key, last_course_note_key)
    sn = na.run_quickstart()

@app.route("/upvote/<key>/<note_type>")
def upvote(key, note_type):
    if note_type == "super_note":
        up = 0 if dm.get_note_key(key)["upvotes"] is None else dm.get_note_key(key)["upvotes"]
        dm.update_data(key, "upvotes", up + 1)
    else:
        up = 0 if notesManager.get_note_key(key)["upvotes"] is None else notesManager.get_note_key(key)["upvotes"]
        notesManager.update_data(key, "upvotes", up + 1)
    return redirect('/index')

@app.route("/downvote/<key>/<note_type>")
def downvote(key, note_type):
    if note_type == "super_note":
        up = 0 if dm.get_note_key(key)["upvotes"] is None else dm.get_note_key(key)["upvotes"]
        dm.update_data(key, "upvotes", up - 1)
    else:
        up = 0 if notesManager.get_note_key(key)["upvotes"] is None else notesManager.get_note_key(key)["upvotes"]
        notesManager.update_data(key, "upvotes", up - 1)
    return redirect('/index')