from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from asgiref.sync import sync_to_async
from events.receiver import state
from workers.dependencies import get_inspect
from workers.models import QueueInfo, ScheduledTask, Stats, TaskRequest, Worker


async def get_workers(request):
    alive = request.GET.get('alive')
    if alive is not None:
        alive = alive.lower() in ['true', '1']

    workers = [
        Worker.from_celery_worker(worker)
        for worker in state.workers.values()
        if alive is None or worker.alive == alive
    ]

    return JsonResponse([worker.model_dump() for worker in workers], safe=False)


@cache_page(5)
async def get_worker_stats(request):
    inspect = await get_inspect()
    stats = await sync_to_async(inspect.stats)() or {}
    return JsonResponse(stats)


@cache_page(5)
async def get_worker_registered(request):
    inspect = await get_inspect()
    registered = await sync_to_async(inspect.registered)() or {}
    return JsonResponse(registered)


@cache_page(5)
async def get_worker_revoked(request):
    inspect = await get_inspect()
    revoked = await sync_to_async(inspect.revoked)() or {}
    return JsonResponse(revoked)


@cache_page(1)
async def get_worker_scheduled(request):
    inspect = await get_inspect()
    scheduled = await sync_to_async(inspect.scheduled)() or {}
    return JsonResponse(scheduled)


@cache_page(1)
async def get_worker_reserved(request):
    inspect = await get_inspect()
    reserved = await sync_to_async(inspect.reserved)() or {}
    return JsonResponse(reserved)


@cache_page(1)
async def get_worker_active(request):
    inspect = await get_inspect()
    active = await sync_to_async(inspect.active)() or {}
    return JsonResponse(active)


@cache_page(5)
async def get_worker_queues(request):
    inspect = await get_inspect()
    queues = await sync_to_async(inspect.active_queues)() or {}
    return JsonResponse(queues)
