# filepath: speech/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .forms import UserProfileForm
from .forms import AudioRecordForm
from .models import AudioRecord
import base64
from django.core.files.base import ContentFile
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from django.conf import settings
import os
import uuid
from pydub import AudioSegment
from .diction_bot import transcribe_with_whisper_local, client
from .models import SpeechReport, UserProfile
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def profile(request):
    return render(request, 'speech/profile.html')

@login_required
def edit_profile(request):
    user_profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'speech/edit_profile.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@csrf_exempt
def upload_audio(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.subscription_type == 'free':
        # Ограничение для бесплатных пользователей
        uploaded_files = AudioRecord.objects.filter(user=request.user).count()
        if uploaded_files >= 5:  # Лимит на 5 файлов
            return redirect('upgrade_subscription')  # Перенаправление на страницу подписки
    # Логика загрузки аудио
    if request.method == 'POST':
        # Если запрос отправлен через форму
        if request.FILES.get('file'):
            audio_file = request.FILES['file']
            audio_record = AudioRecord(user=request.user, file=audio_file)
            audio_record.save()
            return redirect('audio_list')  # Перенаправление на список аудио

        # Если запрос отправлен через AJAX
        try:
            data = json.loads(request.body)
            audio_data = data.get('audioData')
            if audio_data:
                format, audio_str = audio_data.split(';base64,')
                audio_file = ContentFile(base64.b64decode(audio_str), name='recording.wav')
                audio_record = AudioRecord(user=request.user, file=audio_file)
                audio_record.save()
                return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    elif request.method == 'GET':
        return render(request, 'speech/upload_audio.html')

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

def audio_list(request):
    audio_records = AudioRecord.objects.filter(user=request.user)
    return render(request, 'speech/audio_list.html', {'audio_records': audio_records})

def record_audio(request):
    return render(request, 'speech/record_audio.html')

@login_required
def delete_audio(request, pk):
    audio_record = AudioRecord.objects.get(pk=pk, user=request.user)
    audio_record.delete()
    return redirect('audio_list')

def telegram_web_app(request):
    return render(request, 'speech/telegram_web_app.html')

def send_message_to_bot(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        bot_token = settings.TELEGRAM_BOT_TOKEN  # Получаем токен из settings
        chat_id = settings.CHAT_ID  # Получаем chat_id из settings
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return render(request, 'speech/send_message.html', {"success": True})
        else:
            return render(request, 'speech/send_message.html', {"error": "Failed to send message"})
    return render(request, 'speech/send_message.html')

def send_audio_to_bot(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.CHAT_ID
        url = f"https://api.telegram.org/bot{bot_token}/sendVoice"

        # Отправляем аудиофайл в чат с ботом
        files = {'voice': audio_file}
        data = {'chat_id': chat_id}
        response = requests.post(url, data=data, files=files)

        if response.status_code == 200:
            return render(request, 'speech/send_audio_to_bot.html', {"success": True})
        else:
            return render(request, 'speech/send_audio_to_bot.html', {"error": "Failed to send audio"})
    return render(request, 'speech/send_audio_to_bot.html')

def analyze_audio(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        temp_ogg = f"temp_voice_{uuid.uuid4().hex}.ogg"
        temp_wav = temp_ogg.replace(".ogg", ".wav")

        # Сохраняем ogg
        with open(temp_ogg, "wb") as f:
            f.write(audio_file.read())

        # Конвертируем ogg в wav
        try:
            audio = AudioSegment.from_file(temp_ogg)
            audio.export(temp_wav, format="wav")
        except Exception as e:
            return render(request, 'speech/analyze_audio.html', {"error": f"Error converting audio: {str(e)}"})

        # Проверяем, существует ли файл temp_wav
        if not os.path.exists(temp_wav):
            return render(request, 'speech/analyze_audio.html', {"error": "Failed to create WAV file."})

        # Распознаём речь через Whisper
        recognized_text = transcribe_with_whisper_local(temp_wav)

        if not recognized_text.strip():
            return render(request, 'speech/analyze_audio.html', {"error": "Speech could not be recognized."})

        # Расчёт метрик
        try:
            duration = audio.duration_seconds  # Длительность аудио
            wpm = calculate_wpm(recognized_text, duration)
            pauses = calculate_pauses(temp_wav)
            clarity = calculate_clarity(recognized_text, len(recognized_text.split()))

            metrics = {
                "wpm": wpm,
                "pause_count": pauses["pause_count"],
                "total_pause_duration": pauses["total_pause_duration"],
                "clarity": clarity
            }
        except Exception as e:
            return render(request, 'speech/analyze_audio.html', {"error": f"Error calculating metrics: {str(e)}"})

        # Анализируем текст через OpenAI
        completion = client.chat.completions.create(
            model="anthropic/claude-3-sonnet",
            messages=[
                {
                    "role": "user",
                    "content": f"Проанализируй мою дикцию и дай рекомендации по улучшению. Вот текст, который я произнёс: {recognized_text}"
                }
            ]
        )
        analysis = completion.choices[0].message.content

        # Удаляем временные файлы
        for temp_file in [temp_ogg, temp_wav]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return render(request, 'speech/analyze_audio.html', {"text": recognized_text, "analysis": analysis, "metrics": metrics})
    return render(request, 'speech/analyze_audio.html')

def dashboard(request):
    audio_records = AudioRecord.objects.filter(user=request.user)
    return render(request, 'speech/dashboard.html', {'audio_records': audio_records})

def calculate_wpm(text, duration):
    """
    Рассчитывает Words per Minute (WPM).
    :param text: Распознанный текст.
    :param duration: Длительность аудио в секундах.
    :return: WPM (слова в минуту).
    """
    words = len(text.split())  # Количество слов
    duration_minutes = duration / 60  # Переводим длительность в минуты
    if duration_minutes > 0:
        wpm = words / duration_minutes
    else:
        wpm = 0
    return round(wpm, 2)  # Округляем до двух знаков после запятой


def calculate_pauses(audio_path):
    """
    Рассчитывает количество и общую длительность пауз в аудио.
    :param audio_path: Путь к аудиофайлу.
    :return: Словарь с количеством пауз и их общей длительностью.
    """
    try:
        audio = AudioSegment.from_file(audio_path)
        silence_threshold = -40  # Порог тишины (в децибелах)
        min_silence_length = 500  # Минимальная длина тишины (в миллисекундах)

        # Используем split_on_silence для анализа пауз
        silence_chunks = audio.split_to_mono()
        silence_durations = [len(chunk) for chunk in silence_chunks if chunk.dBFS < silence_threshold]

        total_pause_duration = sum(silence_durations) / 1000  # В секундах
        return {
            "pause_count": len(silence_durations),
            "total_pause_duration": round(total_pause_duration, 2)
        }
    except FileNotFoundError:
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    except Exception as e:
        raise Exception(f"Error processing audio file: {str(e)}")


def calculate_clarity(text, total_words):
    """
    Рассчитывает чёткость речи.
    :param text: Распознанный текст.
    :param total_words: Общее количество слов в аудио.
    :return: Процент чёткости.
    """
    recognized_words = len(text.split())
    if total_words > 0:
        clarity = (recognized_words / total_words) * 100
    else:
        clarity = 0
    return round(clarity, 2)

def analysis_history(request):
    reports = SpeechReport.objects.filter(user=request.user).order_by('-created_at')
    
    chart_data = {
        "dates": [report.created_at.strftime("%Y-%m-%d %H:%M:%S") for report in reports],
        "wpm": [report.wpm for report in reports],
        "pause_count": [report.pause_count for report in reports],
        "total_pause_duration": [report.total_pause_duration for report in reports],
        "clarity": [report.clarity for report in reports],
    }
    
    return render(request, 'speech/analysis_history.html', {
        'reports': reports,
        'chart_data': json.dumps(chart_data, cls=DjangoJSONEncoder),
    })

def speech_report_detail(request, report_id):
    report = get_object_or_404(SpeechReport, id=report_id, user=request.user)
    return render(request, 'speech/speech_report_detail.html', {'report': report})

def upgrade_subscription(request):
    return render(request, 'speech/upgrade_subscription.html')
