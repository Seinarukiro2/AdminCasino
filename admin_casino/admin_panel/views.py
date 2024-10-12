from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import User, Project, Settings
from .encryption import decrypt_user_id, encrypt_user_id
from .terminal_creator import TerminalCreator
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from .forms import LoginForm
from asgiref.sync import sync_to_async
import json
import time
import logging
from django.views.decorators.cache import never_cache
from .telegram_bot import start_bot, restart_bot, stop_bot

logger = logging.getLogger('django')

async def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Используем sync_to_async для аутентификации пользователя
            user = await sync_to_async(authenticate)(username=username, password=password)
            
            if user is not None:
                # Если пользователь прошел аутентификацию, выполняем login
                await sync_to_async(login)(request, user)
                return redirect('user_list')  # Перенаправляем на страницу со списком пользователей
            else:
                form.add_error(None, mark_safe("Неправильный логин или пароль"))
    else:
        form = LoginForm()

    return render(request, 'admin_panel/login.html', {'form': form})

# Получаем список пользователей и связанных проектов
async def user_list(request):
    query = request.GET.get('q')
    hall_id_filter = request.GET.get('hall_id')

    # Загружаем всех пользователей с предзагрузкой связанных проектов
    users = await User.all().select_related('project')

    if query:
        users = [user for user in users if query.lower() in user.login.lower() or query.lower() in user.hidden_login.lower()]

    if hall_id_filter:
        users = [user for user in users if user.hall_id == int(hall_id_filter)]

    projects = await Project.all()

    return render(request, 'admin_panel/user_list.html', {
        'users': users,
        'query': query,
        'hall_id_filter': hall_id_filter,
        'projects': projects
    })


# Создаем пользователя через форму
async def create_user_form(request):
    projects = await Project.all()  # Получаем все проекты для отображения hall_id в форме
    return render(request, 'user_form.html', {'projects': projects})

# Создаем тестового пользователя
async def create_test_user(request):
    if request.method == 'POST':
        login = request.POST.get('login')
        password = request.POST.get('password')
        hidden_login = request.POST.get('hidden_login')
        hall_id = request.POST.get('hall_id')

        project = await Project.filter(hall_id=hall_id).first()
        if not project:
            return HttpResponse("Проект с таким hall_id не существует, пользователь не может быть создан", status=400)

        await User.create(
            login=login,
            password=password,
            hidden_login=hidden_login,
            project=project,
            hall_id=project.hall_id
        )

        return redirect('user_list')

    return HttpResponse("Неверный запрос", status=400)

# Список проектов
async def project_list(request):
    
    query = request.GET.get('q')
    hall_id_filter = request.GET.get('hall_id')

    projects = await Project.all().order_by('-id')  # Получаем все проекты

    if query:
        projects = [project for project in projects if query.lower() in project.project_name.lower()]

    if hall_id_filter:
        projects = [project for project in projects if project.hall_id == int(hall_id_filter)]

    return render(request, 'admin_panel/project_list.html', {
        'projects': projects,
        'query': query,
        'hall_id_filter': hall_id_filter
    })

# Создание нового проекта
async def create_project(request):
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project_link = request.POST.get('project_link')
        hall_id = request.POST.get('hall_id')
        mac = request.POST.get('mac')
        bot_username = request.POST.get('bot_username')  

        await Project.create(
            project_name=project_name,
            project_link=project_link,
            hall_id=hall_id,
            mac=mac,
            bot_username=bot_username
        )

        return redirect('project_list')

    return HttpResponse("Неверный запрос", status=400)

# Детали проекта и редактирование
async def project_detail(request, project_id):
    project = await Project.get(id=project_id)
    users = await User.filter(hall_id=project.hall_id).all()  # Получаем пользователей, привязанных к hall_id проекта

    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project_link = request.POST.get('project_link')
        mac = request.POST.get('mac')
        bot_token = request.POST.get('bot_token')
        webapp_url = request.POST.get('webapp_url')
        bot_username = request.POST.get('bot_username')  

        project.project_name = project_name
        project.project_link = project_link
        project.mac = mac
        project.bot_token = bot_token
        project.webapp_url = webapp_url
        project.bot_username = bot_username  # Сохраняем новое поле
        await project.save()

        return redirect('project_detail', project_id=project.id)

    return render(request, 'admin_panel/project_detail.html', {'project': project, 'users': users})


# Удаление проекта
async def delete_project(request, project_id):
    project = await Project.get(id=project_id) 


    if request.method == 'POST':
        # Очищаем hall_id и проект для всех пользователей
        await User.filter(project_id=project_id).update(hall_id=None, project_id=None)
        await project.delete()

        return redirect('project_list')

    return render(request, 'admin_panel/project_detail.html', {'project': project})


@never_cache
async def process_user_id(request):
    if request.method == 'POST':
        print("IM HERE - Start of POST request")
        try:
            data = json.loads(request.body)
            print(f"Request data: {data}")  # Логируем полученные данные
        except json.JSONDecodeError as e:
            print(f"Invalid JSON received: {e}")  # Логируем ошибку JSON
            return JsonResponse({'error': 'Invalid JSON', 'details': str(e)}, status=400)

        decrypted_uid = data.get('uid')
        print(f"Decrypted UID from request: {decrypted_uid}")  # Логируем UID
        if not decrypted_uid:
            print("UID is missing from the request")  # Логируем отсутствие UID
            return JsonResponse({'error': 'UID is required'}, status=400)

        hall_id = data.get('hall_id')
        print(f"Hall ID from request: {hall_id}")  # Логируем Hall ID
        if not hall_id:
            print("Hall ID is missing from the request")  # Логируем отсутствие Hall ID
            return JsonResponse({'error': 'Hall ID is required'}, status=400)

        # Объединяем UID и hall_id без разделительных знаков
        combined_login = f"{decrypted_uid}{hall_id}"
        print(f"Combined login (UID + Hall ID without separator): {combined_login}")  # Логируем объединенный логин

        # Шифрование объединенного логина
        try:
            encrypted_login = encrypt_user_id(combined_login)  # Шифруем объединенный логин
            print(f"Encrypted Login (UID + Hall ID): {encrypted_login}")  # Логируем зашифрованный логин
        except Exception as e:
            print(f"Error encrypting login: {e}")  # Логируем ошибку шифрования
            return JsonResponse({'error': 'Error encrypting login', 'details': str(e)}, status=500)

        logger.info(f"Запрос с hall_id: {hall_id}, зашифрованный login: {encrypted_login}")
        
        # Проверка, существует ли пользователь
        print("IM HERE - Checking if user exists")
        try:
            user = await User.filter(login=encrypted_login).first()
            print(f"User found: {user}") if user else print("User not found")
        except Exception as e:
            print(f"Error finding user: {e}")  # Логируем ошибку поиска пользователя
            return JsonResponse({'error': 'Error finding user', 'details': str(e)}, status=500)
        
        print("IM HERE - Checking if project exists")
        try:
            project = await Project.filter(hall_id=hall_id).first()
            print(f"Project found: {project}") if project else print("Project not found")
        except Exception as e:
            print(f"Error finding project: {e}")  # Логируем ошибку поиска проекта
            return JsonResponse({'error': 'Error finding project', 'details': str(e)}, status=500)

        if user:
            print(f"User {user.login} exists, preparing redirect URL")
            if project and project.project_link:
                # Используем зашифрованный логин и пароль пользователя в редирект-ссылке
                redirect_url = f"{project.project_link}?u={encrypted_login}&p={user.password}&ts={int(time.time())}&tg=True"
                print(f"Redirect URL for existing user: {redirect_url}")  # Логируем редирект
                return JsonResponse({'redirect_url': redirect_url})
            else:
                print(f"Project with hall_id {hall_id} not found")
                return JsonResponse({'error': 'Project with this hall_id not found'}, status=404)
        else:
            print("User does not exist, creating a new one")
            # Если пользователь не найден, создаем нового через TerminalCreator
            if not project:
                print(f"Project with hall_id {hall_id} not found")
                return JsonResponse({'error': 'Project with this hall_id not found'}, status=404)

            print("IM HERE - Initializing TerminalCreator")
            try:
                # Используем зашифрованный логин (UID + Hall ID)
                terminal_creator = TerminalCreator(
                    name=encrypted_login,  # Зашифрованный логин
                    login=encrypted_login,  # Логин в TerminalCreator также зашифрованный
                    mac=project.mac,  # Получаем MAC адрес
                    hall_id=hall_id,
                    api_url="https://apimagnitonline.gamesapi.net"  # URL вашего API для создания терминала
                )
                print("IM HERE - Sending terminal creation request")
                terminal_response = await terminal_creator.create_terminal()
                print(f"Terminal creation response: {terminal_response}")
            except Exception as e:
                print(f"Error creating terminal: {e}")  # Логируем ошибку создания терминала
                return JsonResponse({'error': 'Failed to create terminal', 'details': str(e)}, status=500)

            if not terminal_response:
                print("Terminal creation failed, no response received")
                return JsonResponse({'error': 'Failed to create terminal'}, status=500)

            # Извлекаем password из ответа
            try:
                if isinstance(terminal_response, dict) and 'content' in terminal_response:
                    password = terminal_response['content'].get('password', 'temporary_password')
                    print(f"Password extracted from terminal response: {password}")
                else:
                    print("Invalid response structure from terminal creation")
                    return JsonResponse({'error': 'Invalid response from terminal creation'}, status=500)
            except Exception as e:
                print(f"Error extracting password from terminal response: {e}")  # Логируем ошибку извлечения пароля
                return JsonResponse({'error': 'Error extracting password', 'details': str(e)}, status=500)

            print("IM HERE - Creating new user in the database")
            try:
                new_user = await User.create(
                    login=encrypted_login,  # Логин как объединение UID и hall_id
                    password=password,
                    hidden_login=encrypted_login,  # Используем зашифрованный логин как hidden_login
                    project=project,
                    hall_id=hall_id
                )
                print(f"New user created: {new_user}")
            except Exception as e:
                print(f"Error creating new user: {e}")  # Логируем ошибку создания пользователя
                return JsonResponse({'error': 'Error creating new user', 'details': str(e)}, status=500)

            # Формируем redirect URL для нового пользователя
            redirect_url = f"{project.project_link}?u={new_user.hidden_login}&p={new_user.password}&ts={int(time.time())}&tg=True"
            print(f"Redirect URL for new user: {redirect_url}")  # Логируем редирект
            return JsonResponse({'redirect_url': redirect_url})

    print("Invalid request method, must be POST")
    return JsonResponse({'error': 'Invalid request'}, status=400)
    




# Рендеринг страницы с подключением Telegram Web App SDK
async def telegram_app_view(request, hall_id):
    if request.method == 'GET':

        context = {'hall_id': hall_id}
        return render(request, 'admin_panel/telegram_app.html', context)

async def start_bot_view(request, project_id):
    if request.method == 'POST':
        project = await Project.get(id=project_id)
        if project:
            # Получаем необходимые поля из модели Project
            bot_token = project.bot_token
            welcome_message = project.start_message
            button_url = project.webapp_url
            folder_name = project.bot_username
            screen_name = folder_name

            # Запуск бота
            start_bot(bot_token, welcome_message, button_url, folder_name, screen_name)

            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error'}, status=400)

async def restart_bot_view(request, project_id):
    project = await Project.get(id=project_id)
    if project:
        # Рестарт бота
        restart_bot(project.bot_username)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

async def stop_bot_view(request, project_id):
    project = await Project.get(id=project_id)
    if project:
        # Остановка бота
        stop_bot(project.bot_username)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

async def update_bot_settings(request, project_id):
    project = await Project.get(id=project_id)
    if request.method == 'POST':
        bot_token = request.POST.get('bot_token')
        start_message = request.POST.get('start_message')

        project.bot_token = bot_token
        project.start_message = start_message
        await project.save()

        return redirect('project_detail', project_id=project.id)

    return redirect('project_detail', project_id=project.id)

# Представление для отображения страницы настроек
@user_passes_test(lambda u: u.is_superuser)  # Только для суперпользователей
async def settings_view(request):
    settings = await Settings.first()  # Получаем настройки (или создаем новые, если их нет)
    if not settings:
        settings = await Settings.create(api_id='', api_hash='')
    return render(request, 'admin_panel/settings.html', {'settings': settings})

# Представление для обновления настроек
async def update_settings(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Используем sync_to_async для аутентификации пользователя
        user = await sync_to_async(authenticate)(username=username, password=password)
        
        if user and user.is_superuser:
            api_id = request.POST.get('api_id')
            api_hash = request.POST.get('api_hash')

            # Получаем первую запись из Settings
            settings = await Settings.first()  # Tortoise ORM возвращает именно объект, а не QuerySet
            
            if settings:
                settings.api_id = api_id
                settings.api_hash = api_hash
                await settings.save()  # Сохраняем изменения в базе данных

            return redirect('settings')
        else:
            return render(request, 'admin_panel/login_superuser.html', {'error': 'Неправильные логин или пароль'})

    return redirect('settings')

    