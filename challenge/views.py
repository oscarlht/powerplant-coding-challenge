from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Data
from .powerplant_management import unit_commitment
from . import db
import json
import requests

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        inp = request.form.get('note')
        if "http" in inp:
            response = requests.get(inp)
            payload = json.dumps(response.json())
            output = json.dumps(unit_commitment(response.json()))
        else:
            inp = json.loads(inp)
            payload = json.dumps(inp)
            output = json.dumps(unit_commitment(inp))
        if len(inp) < 1:
            flash('Please enter a correct set of data.', category='error')
        else:
            new_note = Data(data=payload, unit_commitment=output, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Data added!', category='success')
    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Data.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})
