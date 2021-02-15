from flask import Flask, request, jsonify, render_template
import os
# from api.v1 import config
# from api.v1.user import user
from flask_bootstrap import Bootstrap
from db.db import *

app = Flask(__name__)
Bootstrap(app)
# app.config.from_object(config)
# app.register_blueprint(user,url_prefix='/user')

def create_app():
  app = Flask(__name__)
  Bootstrap(app)

  return app

@app.route('/index')
def index():
    userList = fetchUserList()
    return render_template('index.html', userList=userList)

@app.route('/win_lose_detail')
def win_lose_detail():
    userId = request.args.get('userId')

    user = fetchUser(userId) #type:User
    matchList =fetchMatchList(user.id)
    for match in matchList:
        predictList = fetchPredictList(match.id, user.id)
        match.predictList=predictList
    return render_template('win_lose_chart.html', user=user, matchList = matchList)

@app.route('/test')
def test():
    return render_template('bootstrap/google.html')

@app.context_processor
def inject_stage_and_region():
    return dict(stage="alpha", region="NA")

admin_user = {
  "name": "admin",
  "email": "admin@example.com",
  "description": "Some description words"
}

def cal_total_hit_cnt(match:Match):
    hit_cnt=0
    for predict in match.predictList:
        if predict.is_hit=='1':
            hit_cnt=hit_cnt+1
        elif predict.is_hit=='2' and predict.real_result!='3':
            hit_cnt=hit_cnt-1
    return hit_cnt

def convert_tooltip(match:Match):
    labelList=[]
    labelList.append(f"home_team: {match.home_team_name}: {match.home_team_score}")
    labelList.append(f"home_team: {match.away_team_name}: {match.away_team_score}")
    return labelList

# @app.context_processor
# def get_user_list():
#     userList=fetchUserList()
#     return {"userList": userList}

@app.context_processor
def send_my_func():
  return {"cal_total_hit_cnt": cal_total_hit_cnt, "str": str, "enumerate":enumerate, "len":len}

def run():
    app.run(debug=True, port=8088)

if __name__ == '__main__':
    run()