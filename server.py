from flask import Flask, request, jsonify
from flask.views import MethodView
from celery import Celery
from celery.result import AsyncResult
from upscale import upscale
import uuid
import os.path

app_name = 'server'
app = Flask(app_name)
celery = Celery(
    app_name,
    backend='redis://127.0.0.1:6379/3',
    broker='redis://127.0.0.1:6379/4'
)

celery.conf.update(app.config)

class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

@celery.task()
def update_photo(image):
    """
    Запуск функции апскейлинга
    """
    extension = image.split('.')[-1]
    result_file = f'{uuid.uuid4()}.{extension}'
    upscale(image, result_file)
    return result_file

class PhotoUpscale(MethodView):
    """
    Класс описывающий работу с фнукцией апскейлинга по средствам celery
    """

    def get(self, task_id):
        """
        Метод получает id задачи celery и возвращает статус и имя файла
        """
        task = AsyncResult(task_id, app=celery)

        return jsonify({
            'status': task.status,
            'file': task.result
        })

    def post(self):
        """
        Метод получает имя файла для апскейлинга и возвращает id задачи celery
        """
        photo = request.json['image']
        task = update_photo.delay(photo)
        return jsonify(
            {'task_id': task.id}
        )

def processed(file):
    """
    Метод получает имя файла, проверяет его наличие и возвращает абсолютный путь к нему
    """
    res = os.path.exists(file)
    if res:
        return jsonify({'filename': os.path.abspath (file)})
    return jsonify({'filename': 'File not found'})

app.add_url_rule('/upscale', view_func=PhotoUpscale.as_view('photo'), methods=['POST'])
app.add_url_rule('/tasks/<string:task_id>', view_func=PhotoUpscale.as_view('photo_get'), methods=['GET'])
app.add_url_rule('/processed/<file>', view_func=processed, methods=['GET'])


if __name__ == '__main__':
    app.run()