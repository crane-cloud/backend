
import json
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.models import mongo
from bson.json_util import dumps
import uuid

#get activity logs
class ActivityLogsDetailView(Resource):

    @jwt_required
    def get(self, id):

        try:
            
            #validate id
            uuid.UUID(id)

            id = id
            cursor = mongo.db['activities'].find( { "$or":[
                {"user_id":id}, 
                {"a_cluster_id":id},
                {"a_project_id":id},
                {"a_app_id":id},
                {"a_user_id":id},
                {"a_db_id":id}
                ]})
            json_data = dumps(cursor)

            return dict(
                status='success',
                data = dict(logs = json.loads(json_data))
            ), 200
        except Exception as err:
            return dict(status='fail', message=str(err)), 400

        
