# views.py
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from celery.result import AsyncResult
from celery_detect.celery_app import get_celery_app
from events.receiver import state
from tasks.models import Task, TaskResult


async def get_tasks(request):
    limit = int(request.GET.get('limit', 1000))
    offset = int(request.GET.get('offset', 0))

    items = [Task.from_celery_task(task) for _, task in state.tasks_by_time()]
    paginator = Paginator(items, limit)
    page = paginator.get_page(offset // limit + 1)

    response_data = {
        'items': [task.model_dump() for task in page.object_list],
        'total': paginator.count,
        'limit': limit,
        'offset': offset,
    }
    return JsonResponse(response_data)


async def get_task_detail(request, task_id):
    task = state.tasks.get(task_id)
    if task is None:
        raise Http404("Task not found.")

    task_data = Task.from_celery_task(task).to_dict()
    return JsonResponse(task_data)


@cache_page(5)
async def get_task_result(request, task_id):
    celery_app = await get_celery_app()
    result = AsyncResult(task_id, app=celery_app)

    task_result = TaskResult(
        id=result.id,
        type=result.name,
        state=result.state,
        queue=result.queue,
        result=result.result,
        traceback=str(result.traceback) if result.traceback is not None else None,
        ignored=result.ignored,
        args=result.args or [],
        kwargs=result.kwargs or {},
        retries=result.retries or 0,
        worker=result.worker,
    ).model_dump()

    return JsonResponse(task_result)