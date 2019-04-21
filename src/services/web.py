from flask import Flask, jsonify, request
from urllib.parse import urlparse
import logging
import psycopg2
import pika
import sys
import os

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify(success=True)

@app.route("/photos/pending")
def photos_pending():
  fetch = {}
  conn = None
  try:
    url = urlparse(os.environ.get('PG_CONNECTION_URI'))
    db = "dbname=%s user=%s password=%s host=%s " % (url.path[1:], url.username, url.password, url.hostname)
    conn = psycopg2.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT * FROM photos WHERE status = 'pending';")
    fetch = cur.fetchall()
  except (Exception, psycopg2.Error) as error :
    app.logger.error('Error while fetching photos from PostgreSQL', error)
  finally:
    if(conn):
        cur.close()
        conn.close()
  return jsonify(results=fetch)  

@app.route("/photos/process", methods = ['POST'])
def photos_process():
    payload = request.get_json(silent=True)

    if payload == None:
      return jsonify(Sucess=False)

    qconn = None
    results = False

    try:
      url = os.environ.get('AMQP_URI')
      params = pika.URLParameters(url)
      params.socket_timeout = 5

      qconn = pika.BlockingConnection(params)
      channel = qconn.channel()
      channel.queue_declare(queue='photo-processor')
      
      for uuid in payload['payload']:
          channel.basic_publish(exchange='', routing_key='photo-processor', body=uuid)

      results = True
    except (Exception) as error:
      app.logger.error('Error while writing messages to RabbitMQ', error)
    finally:
      if(qconn):
        channel.close()
        qconn.close()
    return jsonify(Sucess=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
