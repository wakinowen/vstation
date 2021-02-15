import pathlib
import urllib

import requests
import urllib3
import csv
import os
import logging
import sys
import datetime
import traceback
from db.db import *
from web import server

REQUEST_CONN_TIMEOUT = 10
REQUEST_READ_TIMEOUT = 60 * 60
HIT_RATE_RECORD_DIR=os.path.join(CURRENT_DIR, "../records")
HIT_RATE_RECORD_FILE_PATH=os.path.join(HIT_RATE_RECORD_DIR, "hit_rate.csv")

SEARCH_URSER_URL="https://mapi.shemen365.com/search/common?type=user&option=%s"
LIST_USER_PREDICT_URL="https://mapi.shemen365.com/user/article/predict/list?uid=%s&page=%s"

USER_ID_LIST=[]

USER_ID_DICT = {'阿拉里奥': 32533, '乌戈': 1331, '克鲁格': 15271,
                '海蒂': 14882, '伊安佩恩': 22392, '季风': 157, '乔伊娜': 2047,
                '杰西卡': 2010, '塞缪尔': 2012, '戈莱奇': 2267, '罗德里戈': 4833,
                '荷兰小飞侠': 29654, '格拉索频道': 2051, '洛维': 15884, '龙扬': 28695,
                '李科林': 28639, '莫妮卡': 13216, '布拉克': 28647, '马尔科-加西亚': 25281}

USER_ID_DICT2 = {"32533": '阿拉里奥',
                 "1331": '乌戈',
                 "15271": '克鲁格',
                 "14882": '海蒂',
                 "22392": '伊安佩恩',
                 "157": '季风',
                 "2047": '乔伊娜',
                 "2010": '杰西卡',
                 "2012": '塞缪尔',
                 "2267": '戈莱奇',
                 "4833": '罗德里戈',
                 "29654": '荷兰小飞侠',
                 "2051": '格拉索频道',
                 "15884": '洛维',
                 "28695": '龙扬',
                 "28639": '李科林',
                 "13216": '莫妮卡',
                 "28647": '布拉克',
                 "25281": '马尔科-加西亚'
                 }

USER_ID_LIST = {32533, 1331, 15271, 14882, 22392, 157, 2047, 2010, 2012, 2267, 4833, 29654, 2051, 15884, 28695, 28639,
                13216, 28647, 25281}

def encodeUri(str):
    # log.info("encoding %s"%str)
    return urllib.parse.quote(str, safe='~@#$&()*!+=:;,.?/\'');

# log=createLogger()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _collect_user_match_info(userId, nick_name):
    user, overMatchList = _collect_user_info(userId)
    for idx, overMatch in enumerate(overMatchList):
        match = Match()  # type: Match
        match.user_id=user.id
        match.user_nick_name = nick_name
        log.info(f"Overmatch idx: {idx}")
        parse_overmatch(userId, match, overMatch)
        save_match(match)
    update_user(user)

def update_user(user:User):
    predictList = fetchPredictListByUid(user.id)
    hit_cnt=0
    total_cnt=0
    for predict in predictList:
        total_cnt=total_cnt+1
        if predict.is_hit=="1":
            hit_cnt=hit_cnt+1
    user.hit_cnt=hit_cnt
    user.total_cnt=total_cnt
    user.hit_rate=round(hit_cnt/total_cnt*100, 2)
    date = datetime.datetime.now().replace(microsecond=0)
    user.date = date
    save_user(user)


def _collect_user_info(userId):
    totalOverMatchList=[]
    userInited=False
    for pageNum in range(1,4):
        listUserPredictUrl = LIST_USER_PREDICT_URL % (userId, str(pageNum))
        res = httpGet(listUserPredictUrl)
        log.info(f"User predict response: {res.text}")
        resJson = res.json()
        overMatchList = resJson["data"]["over_list"]
        if len(overMatchList)==0:
            log.info(f"Page {pageNum} is empty")
            break
        if not userInited:
            author = overMatchList[0]["author"]
            userId = author['uid']
            user = fetchUser(userId)
            if user is None:
                user = User()  # type: User
                user.id = author['uid']
                user.nick_name = author["nick_name"]
            userInited = True
        totalOverMatchList.extend(overMatchList)

    return user, totalOverMatchList

def parse_overmatch(userId:str, match:Match, overMatch):
    # match.article_id = overMatch['article_id']
    match.article_url = overMatch['article_url']
    for idx, match_info in enumerate(overMatch['match_info']):
        parse_match_info(userId, match, match_info, idx)

def parse_match_info(userId:str, match:Match, matchInfo, idx):
    base_info = matchInfo['base_info']
    match.id = base_info['match_id']
    log.info(f"Match id: {match.id}")
    normal_score = base_info['normal_score']
    startTime = base_info['start_time']
    match.match_date = datetime.datetime.fromtimestamp(startTime)
    match.home_team_score = normal_score['team1']
    match.away_team_score = normal_score['team2']
    match.tournament_name= matchInfo['tournament']['tournament_name']
    match.home_team_name = matchInfo['home_team']['team_name']
    match.away_team_name = matchInfo['away_team']['team_name']

    predict = matchInfo['predict']
    matchPredict = Predict()
    matchPredict.id=match.id+"_"+userId +"_"+str(idx)
    matchPredict.match_id=match.id
    matchPredict.user_id=userId
    matchPredict.play_type = predict['play_type']
    matchPredict.predict_result = predict['predict_result']
    matchPredict.real_result = predict['real_result']
    matchPredict.is_hit = predict['is_hit']
    matchPredict.current_left = predict['current_left']
    matchPredict.current_right = predict['current_right']
    matchPredict.current_middle = predict['current_middle']
    matchPredict.ovalue = predict['ovalue']
    save_predict(matchPredict)
    # match.predict.append(matchPredict)


def read_csv():
    current_hit_rate_record_file_path = get_csv_file_path()
    with open(current_hit_rate_record_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='|', fieldnames = CSV_FIELDS)
        next(reader, None)
        for row in reader:
            print(str(row))

def read_last_hit_info_by_name(nick_name):
    current_hit_rate_record_file_path = get_csv_file_path()
    with open(current_hit_rate_record_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='|', fieldnames = CSV_FIELDS)
        for row in reversed(list(reader)):
            if row["Name"]==nick_name:
                return row
        return None

def read_last_hit_info():
    current_hit_rate_record_file_path = get_csv_file_path()
    with open(current_hit_rate_record_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='|', fieldnames = CSV_FIELDS)
        for row in reader: pass
        return row

def write_csv(row_list):
    with open(get_csv_file_path(), 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|')
        writer.writerow(row_list)

def get_csv_file_path():
    current_hit_rate_record_file_path = HIT_RATE_RECORD_FILE_PATH
    return current_hit_rate_record_file_path

def init_csv():
    csv_file_path = get_csv_file_path()
    if os.path.exists(csv_file_path):
        return
    os.makedirs(HIT_RATE_RECORD_DIR, exist_ok=True)
    with open(csv_file_path, 'w', newline='') as outcsv:
        writer = csv.DictWriter(outcsv, fieldnames = CSV_FIELDS)
        writer.writeheader()

def httpGet(url, proxy=None, allowedStatusCodes=[], **kwargs):
    res = requests.get(url, timeout=(REQUEST_CONN_TIMEOUT, REQUEST_READ_TIMEOUT), verify=False, proxies=proxy, **kwargs)
    if len(allowedStatusCodes) > 0:
        if res.status_code not in allowedStatusCodes:
            raise Exception(f"Response status code is {res.status_code}, not in the allowed list: {allowedStatusCodes}")
    return res

def httpPost(url, json, proxy=None, allowedStatusCodes=[], **kwargs):
    res = requests.post(url, json=json, verify=False, timeout=(REQUEST_CONN_TIMEOUT, REQUEST_READ_TIMEOUT), proxies=proxy, **kwargs)
    if len(allowedStatusCodes) > 0:
        if res.status_code not in allowedStatusCodes:
            raise Exception(f"Response status code is {res.status_code}, not in the allowed list: {allowedStatusCodes}")
    return res


def process(nick_name, date, hit_rate, hit_cnt, total_cnt):
    lastRow = read_last_hit_info_by_name(nick_name)
    if lastRow is not None and lastRow["Total_Cnt"]==total_cnt:
        log.info("This record has been recorded, skip")
        return
    write_csv([nick_name, date, hit_rate, hit_cnt, total_cnt])

def searchUser(userName):
    userName= encodeUri(userName)
    searchUserUrl = SEARCH_URSER_URL%userName
    res = httpGet(searchUserUrl)
    log.info(f"Response for user {userName}: {res.text}")
    return res.json()

def fetchUserIdDict(userNames):
    userIdDict = {}
    for userName in userNames:
        try:
            resJson = searchUser(userName)
            users= resJson["data"]
            if len(users)==0:
                log.info(f"User name {userName} not found, please mannualy confirm which user")
            elif len(users)>1:
                log.info(f"User name {userName} has more than one record, please mannualy confirm which user")
            else:
                uid=resJson["data"][0]["data"]["uid"]
                userIdDict[userName]=uid
        except Exception as e:
            # traceback.print_exc()
            log.error("Failed to search user " + userName + ": " + traceback.format_exc())
    return userIdDict

def fetchUsers():
    userNames=["阿拉里奥", "乌戈", "克鲁格", "海蒂", "伊安佩恩","季风","乔伊娜","杰西卡","塞缪尔","戈莱奇",
               "罗德里戈","荷兰小飞侠","格拉索频道","洛维","龙扬","李科林","莫妮卡","布拉克","马尔科-加西亚","阿拉里奥"]
    userIdDict=fetchUserIdDict(userNames)
    log.info(f"userIds: {userIdDict}")

# def refresh_user_info():
#     for userId, nick_name in USER_ID_DICT2.items():
#         try:
#             nick_name, hit_rate, hit_cnt, total_cnt = parse_user_predicate_list(userId, nick_name)
#             date = datetime.datetime.now().replace(microsecond=0)
#             process(nick_name, date, hit_rate, hit_cnt, total_cnt)
#         except Exception as e:
#             log.error("Failed to get user info for user "+str(userId)+": "+str(e))



def collect_user_match_info():
    for userId, nick_name in USER_ID_DICT2.items():
        try:
            _collect_user_match_info(userId, nick_name)
        except Exception as e:
            # traceback.print_exc()
            log.error("Failed to collect user and match info for user "+str(userId)+": "+traceback.format_exc())
        try:
            dbConn.commit()
        except Exception as e:
            log.error("Failed to save to db: " + traceback.format_exc())

def collect_user_info():
    for userId, nick_name in USER_ID_DICT2.items():
        try:
            _collect_user_info(userId)
        except Exception as e:
            # traceback.print_exc()
            log.error("Failed to collect user info for user "+str(userId)+": "+traceback.format_exc())


def main():
    if os.getenv("only_run_web", 'False')!='True':
        collect_user_match_info()
    server.run()


if __name__ == '__main__':
    # create_table_user()
    # collect_user_info()
    main()