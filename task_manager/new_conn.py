import pymysql
from warnings import filterwarnings

filterwarnings('ignore', category=pymysql.Warning)
CONNECT_TIMEOUT = 100
IP = 'localhost'
PORT = 3306
USER = 'root'
PASSSWORD = ''


class QueryException(Exception):
    """
    """


class ConnectionException(Exception):
    """
    """


class MySQL_Utils():
    def __init__(
            self, ip=IP, port=PORT, user=USER, password=PASSSWORD,
            connect_timeout=CONNECT_TIMEOUT, remote=False, socket='', dbname='test'):
        self.__conn = None
        self.__cursor = None
        self.lastrowid = None
        self.connect_timeout = connect_timeout
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.mysocket = socket
        self.remote = remote
        self.db = dbname
        self.rows_affected = 0

    def __init_conn(self):
        try:
            conn = pymysql.connect(
                host=self.ip,
                port=int(self.port),
                user=self.user,
                db=self.db,
                connect_timeout=self.connect_timeout,
                charset='utf8', unix_socket=self.mysocket)
        except pymysql.Error as e:
            raise ConnectionException(e)
        self.__conn = conn

    def __init_cursor(self):
        if self.__conn:
            self.__cursor = self.__conn.cursor(pymysql.cursors.DictCursor)

    def close(self):
        if self.__conn:
            self.__conn.close()
            self.__conn = None

    # 专门处理select 语句
    def find(self, sql, args=None):
        try:
            if self.__conn is None:
                self.__init_conn()
                self.__init_cursor()
            self.__conn.autocommit = True
            self.__cursor.execute(sql, args)
            self.rows_affected = self.__cursor.rowcount
            results = self.__cursor.fetchall()
            return results
        except pymysql.Error as e:
            raise pymysql.Error(e)
        finally:
            if self.__conn:
                self.close()

    # 专门处理dml语句 delete，updete，insert
    def cud(self, sql, args=None):
        try:
            if self.__conn is None:
                self.__init_conn()
                self.__init_cursor()
            if self.__cursor is None:
                self.__init_cursor()
            self.rows_affected = self.__cursor.execute(sql, args)
            self.lastrowid = self.__cursor.lastrowid
            return self.rows_affected
        except pymysql.Error as e:
            raise pymysql.Error(e)
        finally:
            if self.__cursor:
                self.__cursor.close()
                self.__cursor = None

    # 提交
    def commit(self):
        try:
            if self.__conn:
                self.__conn.commit()
        except pymysql.Error as e:
            raise pymysql.Error(e)
        finally:
            if self.__conn:
                self.close()

    # 回滚操作
    def rollback(self):
        try:
            if self.__conn:
                self.__conn.rollback()
        except pymysql.Error as e:
            raise pymysql.Error(e)
        finally:
            if self.__conn:
                self.close()

    # 适用于需要获取插入记录的主键自增id
    def get_lastrowid(self):
        return self.lastrowid

    # 获取dml操作影响的行数
    def get_affectrows(self):
        return self.rows_affected
        # MySQL_Utils初始化的实例销毁之后，自动提交

    def __del__(self):
        self.commit()
