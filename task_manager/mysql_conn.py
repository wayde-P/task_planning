import pymysql as ps

class MysqlHelper:
    def __init__(self, host,  port, user, password, database, charset):
        self.host = host
        self.user = user
        self.port = port
        self.password = password
        self.database = database
        self.charset = charset
        self.db = None
        self.curs = None
    # 数据库连接
    def open(self):
        self.db = ps.connect(host=self.host,
                             user=self.user,
                             port=self.port,
                             password=self.password,
                             database=self.database,
                             charset=self.charset,
                             cursorclass=ps.cursors.DictCursor
                             )
        self.curs = self.db.cursor()

    # 数据库关闭
    def close(self):
        self.curs.close()
        self.db.close()
    # 数据增删改
    def cud(self, sql, params = "noparams"):
        self.open()
        # self.curs.execute(sql)
        # self.db.commit()
        try:
            if params == "noparams" :
                self.curs.execute(sql)
            else:
                self.curs.execute(sql, params)
                print("cud :",sql,params)
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            print("cud :", sql, params)
            print('cud失败')
            self.db.rollback()
            return False
    # 数据查询
    def find(self, sql, params = "noparams"):
        self.open()
        # print(sql, params)
        result_dict = dict()
        try:
            if params == "noparams" :
                self.curs.execute(sql)
            else:
                self.curs.execute(sql, params)
            result_dict = self.curs.fetchall()
            # print("mysql_conn SQL: ",sql,params)
            # print("result_dict : ",result_dict)
            return result_dict
        except Exception as e :
            print(e)
            print('select出现错误')
            return result_dict
