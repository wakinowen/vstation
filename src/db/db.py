import atexit
import sqlite3

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
        self.user_id=None
        self.tournament_name=None
        self.home_team_name=None
        self.away_team_name=None
        self.article_url=None
        self.home_team_score=None
        self.away_team_score=None
        self.predict=[]


class Predict:
    def __init__(self):
        self.id=None
        self.match_id=None
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




def create_dbs():
    create_table_match_sql = """
    create table match(
        id integer primary key autoincrement,
        match_date datetime,
        user_nick_name varchar(256),
        user_id varchar(256),
        home_team_name varchar(256),
        away_team_name varchar(256),
        article_url varchar(256),
        home_team_score varchar(256),
        away_team_score varchar(256),
        tournament_name varchar(256),
    )
    """
    cursor.execute(create_table_match_sql)

    create_table_predict_sql = """
        create table predict(
            id varchar(50) primary key,
            match_id varchar(256),
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

def save_user(user:User):
    sql=f"""
        insert into user 
        (id,nick_name,hit_rate,hit_cnt,total_cnt,date)
        values(?,?,?,?,?,?)
        """
    cursor.execute(sql,
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
    sql = f"""
            insert into match 
            (id,match_date,user_nick_name,user_id,tournament_name,home_team_name,away_team_name,
            article_url,home_team_score,away_team_score)
            values(?,?,?,?,?,?,?,?,?,?)
            """
    cursor.execute(sql,
       [
           match.id,
           match.match_date,
           match.user_nick_name,
           match.user_id,
           match.tournament_name,
           match.home_team_name,
           match.away_team_name,
           match.article_url,
           match.home_team_score,
           match.away_team_score
       ]
   )

def save_predict(predict:Predict):
    sql = f"""
            insert into match 
            (id,match_id,
            play_type,predict_result,real_result,is_hit,
            current_left,current_right,current_middle,ovalue)
            values(?,?,?,?,?,?,?,?,?,?)
            """
    cursor.execute(sql,
            [
                predict.id,
                predict.match_id,
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

if __name__ == '__main__':
    create_dbs()