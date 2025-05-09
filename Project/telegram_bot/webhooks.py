from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from telegram_bot.bot import setup_bot
import logging

logger = logging.getLogger(__name__)

# Инициализируем бота один раз при загрузке модуля
bot = setup_bot()

@csrf_exempt
async def telegram_webhook(request):
    if request.method == 'POST':
        try:
            json_data = json.loads(request.body)
            update = Update.de_json(json_data, bot.bot)
            await bot.process_update(update)
            return HttpResponse()
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error'}, status=500)
    return JsonResponse({'status': 'error'}, status=400)