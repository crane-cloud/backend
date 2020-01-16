from flask import Response

def construct_response(json_data):
    return Response(json_data, mimetype='application.json')