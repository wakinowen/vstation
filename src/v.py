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

CURRENT_DIR=os.path.dirname(os.path.realpath(__file__))
REQUEST_CONN_TIMEOUT = 10
REQUEST_READ_TIMEOUT = 60 * 60
HIT_RATE_RECORD_DIR=os.path.join(CURRENT_DIR, "../records")
HIT_RATE_RECORD_FILE_PATH=os.path.join(HIT_RATE_RECORD_DIR, "hit_rate.csv")

SEARCH_URSER_URL="https://mapi.shemen365.com/search/common?type=user&option=%s"
LIST_USER_PREDICT_URL="https://mapi.shemen365.com/user/article/predict/list?uid=%s&page=1"

USER_ID_LIST=[]

CSV_FIELDS = ["Name", "Date", "Hit_Rate", "Hit_Cnt", "Total_Cnt"]


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



def createLogger(stdout=True):
    formatter = "%(asctime)s [%(levelname)s]\t%(module)s:%(lineno)d\t%(message)s"

    handler = None
    appName = "VStation"
    logger = logging.getLogger(appName)
    if (stdout is False):
        handler = logging.FileHandler(CURRENT_DIR + "/" + appName + ".log")
        logger.setLevel(logging.DEBUG)
    else:
        handler = logging.StreamHandler(sys.stdout)
        logger.setLevel(logging.DEBUG)

    handler.setFormatter(logging.Formatter(formatter))
    logger.addHandler(handler)
    return logger


log=createLogger()


def encodeUri(str):
    # log.info("encoding %s"%str)
    return urllib.parse.quote(str, safe='~@#$&()*!+=:;,.?/\'');



# log=createLogger()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parse_user_predicate_list(userId, nick_name):
    listUserPredictUrl=LIST_USER_PREDICT_URL%userId
    res = httpGet(listUserPredictUrl)
    log.info(f"User predict response: {res.text}")
    resJson = res.json()
    overMatchList = resJson["data"]["over_list"]
    for overMatch in overMatchList:
        match = Match()  # type: Match
        match.user_nick_name = nick_name
        match.user_id = userId
        parse_overmatch(match, overMatch)
        save_match(match)

    user= User() # type: User
    author = overMatchList[0]["author"]
    user.hit_rate = author["hit_rate"]
    hit_rate_desc=author["hit_rate_desc"]
    idx1= hit_rate_desc.index("近")
    idx2 = hit_rate_desc.index("中")
    user.total_cnt=hit_rate_desc[idx1+1:idx2]
    user.hit_cnt=hit_rate_desc[idx2+1:]
    user.nick_name=author["nick_name"]
    date = datetime.datetime.now().replace(microsecond=0)
    user.date=date
    save_user(user)

def parse_overmatch(match:Match, overMatch):
    article_url = overMatch['article_url']
    match.article_url = article_url
    idx=0
    for match_info in overMatch['match_info']:
        parse_match_info(match, match_info, idx)
        idx=idx+1

def parse_match_info(match:Match, matchInfo, idx):
    base_info = matchInfo['base_info']
    match.id = base_info['match_id']
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
    matchPredict.id=match.id+"_"+str(idx)
    matchPredict.match_id=match.id
    matchPredict.play_type = predict['play_type']
    matchPredict.predict_result = predict['predict_result']
    matchPredict.real_result = predict['real_result']
    matchPredict.is_hit = predict['is_hit']
    matchPredict.current_left = predict['current_left']
    matchPredict.current_right = predict['current_right']
    matchPredict.current_middle = predict['current_middle']
    matchPredict.ovalue = predict['ovalue']
    save_match()
    match.predict.append(matchPredict)


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



def refresh_user_info():
    for userId, nick_name in USER_ID_DICT2.items():
        try:
            parse_user_predicate_list(userId, nick_name)
        except Exception as e:
            # traceback.print_exc()
            log.error("Failed to get user info for user "+str(userId)+": "+traceback.format_exc())


def init_db():
    current_file_dir = pathlib.Path(__file__).parent.absolute()
    if not os.path.exists(os.path.join(current_file_dir, "../vstation.db")):
        create_dbs()


def main():
    # init_csv()
    init_db()
    refresh_user_info()

if __name__ == '__main__':
    main()
    # parse_user_predicate_list(32533)
    # fetchUsers()