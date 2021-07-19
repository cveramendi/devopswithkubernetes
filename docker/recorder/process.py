import os
import time
import pymysql
import logging
from redis import Redis

redis_params = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('REDIS_PORT', 6379)),
    'db': int(os.environ.get('REDIS_DB', 0))
}

mysql_params = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_ROOT_PASSWORD', '')
}


def init_mysql(params):
    tries = 10
    for i in range(tries):
        try:
            conn = pymysql.connect(**params)
            break
        except pymysql.err.OperationalError as ex:
            time.sleep(5 * (i + 1))
            continue
        else:
            raise ex
    else:
        raise RuntimeError("Cannot connet to mysql db")

    conn.query("CREATE DATABASE IF NOT EXISTS kiosk;")
    conn.select_db('kiosk')
    conn.query("".join((
        "CREATE TABLE IF NOT EXISTS `sellinglog` ( ",
        "`id` int(11) NOT NULL AUTO_INCREMENT, ",
        "`ts` VARCHAR(16) NOT NULL, PRIMARY KEY (`id`) )",
        " ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin AUTO_INCREMENT=1;"
    )))
    conn.commit()
    return conn


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('recorder')
    mysql_conn = init_mysql(mysql_params)
    r = Redis(**redis_params)
    sub = r.pubsub()
    sub.subscribe('selling_timestamp')
    logger.info('Initialized, starting to subscribe redis topic')
    while True:
        for item in sub.listen():
            print(item)
            if item['type'] == 'message':
                data = item['data'].decode()
                logger.info('Got message: {0}'.format(data))
                mysql_conn.query(
                    "INSERT INTO sellinglog (`ts`) VALUES ('{0}');".format(data))
                mysql_conn.commit()
