import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from events.receiver import state
from server_info.debug_bundle import create_debug_bundle
from server_info.models import ClientDebugInfo, ServerInfo
from ws.managers import events_manager
from asgiref.sync import sync_to_async


@sync_to_async
def create_server_info(request):
    return ServerInfo.create(request, state)


@csrf_exempt
async def get_server_info(request):
    # 使用同步函数来创建ServerInfo
    server_info = await create_server_info(request)
    return JsonResponse(server_info)


@csrf_exempt
async def get_clients(request):
    clients = list(events_manager.get_clients())
    clients_data = [client.model_dump() for client in clients]  # Assuming `to_dict` method exists
    return JsonResponse(clients_data, safe=False)


@csrf_exempt
async def clear_state(request):
    force = request.POST.get('force', 'false').lower() in ['true', '1', 'yes']
    state.clear(ready=not force)
    return JsonResponse({"success": True})


@csrf_exempt
async def download_debug_bundle(request):
    client_info_data = json.loads(request.body)
    client_info = ClientDebugInfo(**client_info_data)
    buffer = await create_debug_bundle(request, client_info)
    response = StreamingHttpResponse(
        buffer, content_type='application/zip'
    )
    response['Content-Disposition'] = 'attachment; filename=debug_bundle.zip'
    return response
