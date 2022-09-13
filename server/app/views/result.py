from flask import Blueprint
from app.workflow import flow
from app.models import *
from app import db

result = Blueprint('result', __name__)

@result.route('/generate/<session_name>', methods=['POST'])
def generate_result(session_name):
    return 'generate result'

@result.route('/query/<session_name>', methods=['GET'])
def query_result(session_name):
    return flow.api_flow("https://catfact.ninja/fact")