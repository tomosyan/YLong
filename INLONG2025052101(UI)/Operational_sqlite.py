import sqlite3
from memory_profiler import profile

conn = sqlite3.connect('Inf.db', check_same_thread=False)


class Sqlite:

    # 创建一个游标来执行SQL语句

    def __int__(self):
        # 连接到数据库（如果不存在则创建）
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        conn.close()

    def initialize(self, sql, table_sql):  # 创建表格（如果表格不存在）
        status = None
        cursor = conn.cursor()
        cursor.execute(table_sql)
        if not cursor.fetchone():
            cursor.execute(sql)
            status = "no indication"
        cursor.close()
        return status

    def insert_dates(self, sql, date):  # 批量添加数据
        try:
            # Fill the table
            cursor = conn.cursor()
            # sql = "insert into " + str(table) + " " + str(name) + " values (" + len(name) * '?,' + ")"
            cursor.executemany(sql, date)
            conn.commit()
            cursor.close()
            return "ok", sql
        except sqlite3.Error as e:
            return "err", e
        except Exception as e:
            return "err", e

    def insert_date(self, table, name, value):  # 添加一个记录
        try:
            cursor = conn.cursor()
            insert_query = "insert into " + str(table) + " " + str(name) + " values (?, ?, ?)"
            print(insert_query)
            cursor.execute(insert_query, value)
            conn.commit()
            cursor.close()
            return 'ok', insert_query
        except sqlite3.Error as e:
            return "err", e
        except Exception as e:
            return "err", e

    def delete_date(self, user_id):  # 删除一条记录
        try:
            cursor = conn.cursor()
            delete_query = '''
            DELETE FROM users WHERE id = ?
            '''
            cursor.execute(delete_query, (user_id,))
            conn.commit()
            cursor.close()
        except sqlite3.Error as e:
            return "err", e
        except Exception as e:
            return "err", e

    def update_date(self, sql):  # 更新一条记录
        try:
            cursor = conn.cursor()
            # update_query = "UPDATE " + str(table) +" SET name = ?, age = ? WHERE id = ?"
            cursor.execute(sql)
            conn.commit()
            cursor.close()
            return 'ok', sql
        except sqlite3.Error as e:
            return "err", e
        except Exception as e:
            return "err", e

    def select_date(self, sql):  # 查询所有记录
        try:
            cursor = conn.cursor()
            Value = []
            select_query = sql
            cursor.execute(select_query)
            rows = cursor.fetchall()
            for row in rows:
                Value.append(row)
            cursor.close()
            return 'ok', Value
        except sqlite3.Error as e:
            return "err", e
        except Exception as e:
            return "err", e


if __name__ == "__main__":
    c = Sqlite()
    sel = c.select_date("SELECT ID, title, status FROM print_information")
    for i in range(len(sel[1])):
        sel[1][i] = (str(sel[1][i][0]) + "、" + sel[1][i][1], sel[1][i][2])
    print(sel[1])
    # v = [['pfb', '-19.965', '[mm]<1B>', '2023-08-10 17:06:07'], ['iq', '-0.354', '[A]<40>', '2023-08-10 17:06:07'], ['ve', '0.000', '[mm/s]<42>', '2023-08-10 17:06:07'], ['pe', '0.000', '[mm]<A0>', '2023-08-10 17:06:07'], ['st', 'Drive', 'Active<76>', '2023-08-10 17:06:07'], ['vbusreadout', '324', '[V]<C7>', '2023-08-10 17:06:07'], ['hwpext', '-561', '[counts]<3D>', '2023-08-10 17:06:07']]
    #
    # c = Sqlite()
    # # a = c.select_all_date(table="ARGUMENT")
    # # print(a)
    # b = c.update_date("UPDATE Video_save_Settings SET value = 'Ture' WHERE name = 'save_video'")
    # d = c.select_date("SELECT [Order] FROM BROKEN_BLACKED_MATERIAL WHERE Name='duanliao'")
    # d = c.insert_dates("insert into 'MOTOR_PARAMETER' (name, value, unit, time) values (?,?,?,?)",v)
    # print(d)
    # sel = c.select_date(
    #     "SELECT * FROM Video_save_Settings")
    # print(sel)