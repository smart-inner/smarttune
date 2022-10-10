from flask import Blueprint
from flask import render_template

from .. import db
from .. import models

account = Blueprint('account', __name__, template_folder='templates')

@account.route('/create', methods=['POST'])
def create_account():
    return render_template('hello.html', name='jack')