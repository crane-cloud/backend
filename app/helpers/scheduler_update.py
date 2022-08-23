from datetime import datetime
import json
from datetime import date, datetime
from app.models.credits import Credit
from app.schemas import CreditAssignmentSchema
from app.models.credit_assignments import CreditAssignment
import sqlalchemy
from sqlalchemy import extract, func, and_
from app.models import db
from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

def UpdateCredit(app):
    
        """
        """
        app.app_context().push()
        db.create_all()
        

        
        credit_assignment_schema = CreditAssignmentSchema(many = True)

        todays_datetime = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
        #         SELECT c.user_id, c.amount,  u.expiry_date
        # FROM   credits c
        #    left join(
        #     SELECT  user_id, max(expiry_date) as expiry_date
        #     FROM   credit_assignments 
        #     GROUP  BY user_id
        #     ) u ON u.user_id  = c.user_id  where cast(u.expiry_date as date)   = current_date and c.amount != 0;
	


        try:
            sq = db.session.query(CreditAssignment.user_id, func.max(CreditAssignment.expiry_date).label('expiry_date')).group_by(CreditAssignment.user_id).subquery()
            
            
            credit_assignment_records= db.session.query(Credit.user_id, Credit.amount, sq.c.expiry_date).join(sq,and_(Credit.user_id == sq.c.user_id)).filter(extract('month', sq.c.expiry_date) == datetime.today().month,extract('year', sq.c.expiry_date) == datetime.today().year,extract('day', sq.c.expiry_date) == datetime.today().day,
                                Credit.amount!= 0)
                
            print(type(credit_assignment_records))
            credit_assignments_json, errors = credit_assignment_schema.dumps(credit_assignment_records)
            
            arr= json.loads(credit_assignments_json)
            
           
            if len(arr)>0:
                for i in arr:
                    # update query
                    sql = db.session.query(Credit).filter(Credit.user_id == i['user_id'], Credit.amount == i['amount']).update({Credit.amount:0}, synchronize_session = False)
                    db.session.commit()

                    

        except SQLAlchemyError as e:
            return dict(status='Fail',
                        message='Internal server error'), 500

        