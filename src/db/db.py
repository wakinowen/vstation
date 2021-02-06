import atexit
import logging
import os
import sqlite3
import sys
import traceback

CURRENT_DIR=os.path.dirname(os.path.realpath(__file__))

DB_INSERT_STRATEGY_DELETE_THEN_INSERT="DB_INSERT_STRATEGY_DELETE_THEN_INSERT"
DB_INSERT_STRATEGY_SKIP_INSERT_IF_EXIST="DB_INSERT_STRATEGY_SKIP_INSERT_IF_EXIST"

DB_INSERT_STRATEGY=DB_INSERT_STRATEGY_SKIP_INSERT_IF_EXIST

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

def commit():
    dbConn.commit()
    dbConn.close()

def get_db_conn():
    conn = sqlite3.connect("../vstation.db")
    atexit.register(commit)
    return conn

dbConn = get_db_conn()
cursor = dbConn.cursor()



class Match:
    def __init__(self):
        self.id=None
        self.match_date=None
        self.user_nick_name=None
        self.tournament_name=None
        self.home_team_name=None
        self.away_team_name=None
        self.article_id = None
        self.article_url=None
        self.home_team_score=None
        self.away_team_score=None
        self.predict=[]


class Predict:
    def __init__(self):
        self.id=None
        self.match_id=None
        self.user_id=None
        self.play_type = None  # 1: 正常;  2:让球 0.25;
        self.predict_result = None  # 1: home team win; 2: away team win
        self.real_result = None  # 1: home team win; 2: away team win
        self.is_hit = None  # 1: hit bang; 2: nope
        self.current_left=None
        self.current_right=None
        self.current_middle=None
        self.ovalue=None

class User:
    def __init__(self):
        self.id=None
        self.nick_name=None
        self.hit_rate=None
        self.hit_cnt=None
        self.total_cnt=None
        self.date=None



def recreate_dbs():
    drop_tabls_match="drop table match"
    drop_table_predict="drop table predict"
    drop_table_user="drop table user"
    cursor.execute(drop_tabls_match)
    cursor.execute(drop_table_predict)
    cursor.execute(drop_table_user)
    create_dbs()

def create_dbs():
    create_table_match_sql = """
    create table match(
        id integer primary key autoincrement,
        match_date datetime,
        user_nick_name varchar(256),
        home_team_name varchar(256),
        away_team_name varchar(256),
        article_url varchar(256),
        home_team_score varchar(256),
        away_team_score varchar(256),
        tournament_name varchar(256)
    )
    """
    cursor.execute(create_table_match_sql)

    create_table_predict_sql = """
        create table predict(
            id varchar(256) primary key,
            match_id integer,
            user_id integer,
            play_type varchar(256),
            predict_result varchar(256),
            real_result varchar(256),
            is_hit varchar(256),
            current_left varchar(256),
            current_right varchar(256),
            current_middle varchar(256),
            ovalue varchar(256)
        )
        """
    cursor.execute(create_table_predict_sql)

    create_table_user_sql = """
        create table user(
            id integer primary key autoincrement,
            nick_name varchar(256),
            hit_rate varchar(256),
            hit_cnt varchar(256),
            total_cnt varchar(256),
            date datetime
        )
    """
    cursor.execute(create_table_user_sql)
    dbConn.commit()

def save_user(user:User):
    if DB_INSERT_STRATEGY == DB_INSERT_STRATEGY_DELETE_THEN_INSERT:
        deleteSql = "delete from user where id=?"
        execute_sql(deleteSql, [user.id])
    elif DB_INSERT_STRATEGY == DB_INSERT_STRATEGY_SKIP_INSERT_IF_EXIST:
        selectSql="select * from user where id=?"
        result = fetch_all(selectSql, [user.id])
        if len(result)>0:
            log.info(f"Skip inserting user id: {user.id}, name: {user.nick_name}")
            return

    sql=f"""
        insert into user 
        (id,nick_name,hit_rate,hit_cnt,total_cnt,date)
        values(?,?,?,?,?,?)
        """
    execute_sql(sql,
        [
            user.id,
            user.nick_name,
            user.hit_rate,
            user.hit_cnt,
            user.total_cnt,
            user.date
        ]
    )

def save_match(match:Match):
    if DB_INSERT_STRATEGY == DB_INSERT_STRATEGY_DELETE_THEN_INSERT:
        deleteSql = "delete from match where id=?"
        execute_sql(deleteSql, [match.id])
    elif DB_INSERT_STRATEGY == DB_INSERT_STRATEGY_SKIP_INSERT_IF_EXIST:
        selectSql="select * from match where id=?"
        result = fetch_all(selectSql, [match.id])
        if len(result)>0:
            log.info(f"Skip inserting match id: {match.id}")
            return

    sql = f"""
            insert into match 
            (id,match_date,user_nick_name,tournament_name,home_team_name,away_team_name,
            article_url,home_team_score,away_team_score)
            values(?,?,?,?,?,?,?,?,?)
            """
    execute_sql(sql,
       [
           match.id,
           match.match_date,
           match.user_nick_name,
           match.tournament_name,
           match.home_team_name,
           match.away_team_name,
           match.article_url,
           match.home_team_score,
           match.away_team_score
       ]
   )

def save_predict(predict:Predict):
    if DB_INSERT_STRATEGY == DB_INSERT_STRATEGY_DELETE_THEN_INSERT:
        deleteSql = "delete from predict where id=?"
        execute_sql(deleteSql, [predict.id])
    elif DB_INSERT_STRATEGY == DB_INSERT_STRATEGY_SKIP_INSERT_IF_EXIST:
        selectSql="select * from predict where id=?"
        result = fetch_all(selectSql, [predict.id])
        if len(result)>0:
            log.info(f"Skip inserting predict id: {predict.id}")
            return

    sql = f"""
            insert into predict 
            (id, match_id,user_id,
            play_type,predict_result,real_result,is_hit,
            current_left,current_right,current_middle,ovalue)
            values(?,?,?,?,?,?,?,?,?,?,?)
            """
    execute_sql(sql,
            [
                predict.id,
                predict.match_id,
                predict.user_id,
                predict.play_type,
                predict.predict_result,
                predict.real_result,
                predict.is_hit,
                predict.current_left,
                predict.current_right,
                predict.current_middle,
                predict.ovalue
            ]
        )

def execute_sql(sql, param=None):
    try:
        if param is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, param)
        dbConn.commit()
    except sqlite3.IntegrityError as sie:
        log.error("IntegrityError issue: "+traceback.format_exc())
        raise sie
    except Exception as e:
        log.error("Exception: "+traceback.format_exc())
        raise e

def fetch_all(sql, param=None):
    try:
        if param is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, param)
        result = cursor.fetchall()
        return result
    except sqlite3.IntegrityError as sie:
        log.error("IntegrityError issue: "+traceback.format_exc())
        raise sie
    except Exception as e:
        log.error("Exception: "+traceback.format_exc())
        raise e

if __name__ == '__main__':
    create_dbs()