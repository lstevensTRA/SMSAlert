from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from ..models import Keyword
from .. import db

keywords_bp = Blueprint('keywords', __name__)

@keywords_bp.route('/keywords', methods=['GET', 'POST'])
@login_required
def keywords():
    if request.method == 'POST':
        # Add new keyword
        text = request.form['text']
        match_type = request.form['match_type']
        severity = request.form['severity']
        routing_tag = request.form['routing_tag']
        k = Keyword(text=text, match_type=match_type, severity=severity, routing_tag=routing_tag)
        db.session.add(k)
        db.session.commit()
        return redirect(url_for('keywords.keywords'))
    keywords = Keyword.query.all()
    return render_template('keywords.html', keywords=keywords)

@keywords_bp.route('/keywords/delete/<int:id>')
@login_required
def delete_keyword(id):
    k = Keyword.query.get(id)
    if k:
        db.session.delete(k)
        db.session.commit()
    return redirect(url_for('keywords.keywords')) 