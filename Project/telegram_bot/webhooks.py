from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from aiogram import types
from telegram_bot.bot import dp
import json

@csrf_exempt
async def telegram_webhook(request):
    if request.method == 'POST':
        update = types.Update.to_object(json.loads(request.body))
        await dp.process_update(update)
        return HttpResponse()
    return JsonResponse({'status': 'error'}, status=400)