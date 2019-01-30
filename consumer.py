from pathlib import Path
from wand.image import Image

import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='dryjah-pictures', durable=True)
channel.queue_bind(
    queue='dryjah-pictures', exchange='direct-dryjah', routing_key='pictures')


def callback(ch, method, properties, body):
    body = body.decode('utf8')
    p = Path(body)
    thumbnails_path = Path('./static/nails/')
    with Image(filename=body) as img:
        img.liquid_rescale(64, 64)
        img.format = 'jpeg'
        path = thumbnails_path / p.name
        print(str(path))
        img.save(filename=str(path) + '.jpg')
    log = "File {} added.".format(body)
    print(log)
    channel.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_consume(callback, queue='dryjah-pictures', no_ack=False)

channel.start_consuming()
