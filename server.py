from flask import Flask, request, jsonify
from flask.views import MethodView
from celery import Celery
from celery.result import AsyncResult
from upscale import upscale
import uuid

app_name = 'app'
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
    extension = image.split('.')[-1]
    upscale(image, f'{uuid.uuid4()}.{extension}')

class PhotoUpscale(MethodView):

    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        status = str(task.status)
        result = str(task.result)
        # return jsonify(status)
        return jsonify({'status': status,
                        'result': result})

    def post(self):
        photo = request.json['image']
        task = update_photo.delay(photo)
        return jsonify(
            {'task_id': task.id}
        )

app.add_url_rule('/upscale', view_func=PhotoUpscale.as_view('photo'), methods=['POST'])
app.add_url_rule('/tasks/<string:task_id>', view_func=PhotoUpscale.as_view('photo_get'), methods=['GET'])


if __name__ == '__main__':
    app.run()