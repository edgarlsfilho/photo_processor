#!/usr/bin/env python

from urllib.parse import urlparse
from PIL import Image
import uuid
import urllib.request
import psycopg2
import psycopg2.extras
import pika
import os

def process_photo(body):
    conn = None
    rowcount = 0
    try:
        url = urlparse(os.environ.get('PG_CONNECTION_URI'))
        db = "dbname=%s user=%s password=%s host=%s " % (url.path[1:], url.username, url.password, url.hostname)
        conn = psycopg2.connect(db)

        #register uuid data type for psycopg2 
        psycopg2.extras.register_uuid()

        cur = conn.cursor()
        cur.execute("UPDATE photos SET status = 'processing' WHERE uuid = %s;" % psycopg2.extensions.adapt(uuid.UUID(body)).getquoted().decode())
        rowcount = cur.rowcount
        conn.commit()

        if(rowcount > 0):
            cur.execute("SELECT url FROM photos WHERE uuid = %s;" % psycopg2.extensions.adapt(uuid.UUID(body)).getquoted().decode())
            fetch = cur.fetchall()

            with urllib.request.urlopen(fetch[0][0]) as response, open(body + ".jpg", 'wb') as out_file:
                data = response.read() 
                out_file.write(data)

            output_filename = "/waldo-app-thumbs/" + body + ".jpg"
            size = 320, 320

            im = Image.open(body + ".jpg")
            im.thumbnail(size, Image.ANTIALIAS)
            im.save(output_filename, "JPEG")
            width, height = im.size

            cur.execute("INSERT INTO photo_thumbnails (photo_uuid, width, height, url) VALUES (%s, %s, %s, %s);", 
            (uuid.UUID(body),width, height, output_filename))
            conn.commit()

            cur.execute("UPDATE photos SET status = 'completed' WHERE uuid = %s;" % psycopg2.extensions.adapt(uuid.UUID(body)).getquoted().decode())
            conn.commit()
    except (Exception) as error:
        if (conn and rowcount != None and rowcount > 0):
            cur.execute("UPDATE photos SET status = 'failed' WHERE uuid = %s;" % psycopg2.extensions.adapt(uuid.UUID(body)).getquoted().decode())
            conn.commit()
        print("Error processing photo %s - %s" % (body, error))
    finally:
        if(conn):
            cur.close()
            conn.close()

def on_message(channel, method_frame, header_frame, body):
    process_photo(body.decode())
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

url = os.environ.get('AMQP_URI')
params = pika.URLParameters(url)
params.socket_timeout = 5

qconn = pika.BlockingConnection(params)
channel = qconn.channel()
channel.queue_declare(queue='photo-processor')

channel.basic_consume('photo-processor', on_message)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()

qconn.close()