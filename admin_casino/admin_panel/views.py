from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import User, Project
from .encryption import decrypt_user_id, encrypt_user_id
from .terminal_creator import TerminalCreator
from django.conf import settings
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from asgiref.sync import sync_to_async
import json
import logging


logger = logging.getLogger('django')

async def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Используем sync_to_async для синхронных операций
            user = await sync_to_async(authenticate)(request, username=username, password=password)
            if user is not None:
                await sync_to_async(login)(request, user)
                return redirect('user_list')
            else:
                form.add_error(None, "Неправильный логин или пароль")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

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
        bot_username = request.POST.get('bot_username')  # Новое поле

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
        bot_username = request.POST.get('bot_username')  # Новое поле

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



async def process_user_id(request):
    if request.method == 'POST':
        print("IM HERE")
        try:
            data = json.loads(request.body)
            print(f"Request data: {data}")  # Логируем полученные данные
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON', 'details': str(e)}, status=400)

        decrypted_uid = data.get('uid')
        print(f"Encrypted UID: {decrypted_uid}")
        if not decrypted_uid:
            return JsonResponse({'error': 'UID is required'}, status=400)

        # Зашифровка user_id

        encrypted_user_id = encrypt_user_id(decrypted_uid)
        print(f"Encrypted UID: {decrypted_uid}")

        hall_id = data.get('hall_id')
        logger.info(f"Запрос с hall_id: {hall_id}, зашифрованный user_id: {encrypted_user_id}")
        print("IM HERE")
        # Проверка, существует ли пользователь
        user = await User.filter(login=decrypted_uid).first()
        project = await Project.filter(hall_id=hall_id).first()
        print("IM HERE")
        if user:
            if project and project.project_link:
                # Используем hidden_login и password пользователя
                redirect_url = f"{project.project_link}?u={user.hidden_login}&p={user.password}"
                print(redirect_url)
                return JsonResponse({'redirect_url': redirect_url})
            else:
                return JsonResponse({'error': 'Project with this hall_id not found'}, status=404)
        else:
            # Если пользователь не найден, создаем нового через TerminalCreator
            if not project:
                return JsonResponse({'error': 'Project with this hall_id not found'}, status=404)

            terminal_creator = TerminalCreator(
                name=encrypted_user_id,
                login=encrypted_user_id,
                mac=project.mac,  # Получите или задайте MAC адрес
                hall_id=hall_id,
                api_url="https://apimagnitonline.gamesapi.net"  # URL вашего API для создания терминала
            )

            terminal_response = await terminal_creator.create_terminal()

            if not terminal_response:
                return JsonResponse({'error': 'Failed to create terminal'}, status=500)

            # Извлекаем password из ответа
            if isinstance(terminal_response, dict) and 'content' in terminal_response:
                password = terminal_response['content'].get('password', 'temporary_password')
            else:
                return JsonResponse({'error': 'Invalid response from terminal creation'}, status=500)

            # Создаем нового пользователя в базе данных
            new_user = await User.create(
                login=decrypted_uid,
                password=password,
                hidden_login=encrypted_user_id,  # Используем зашифрованный user_id как hidden_login
                project=project,
                hall_id=hall_id
            )

            # Формируем redirect URL для нового пользователя
            redirect_url = f"{project.project_link}?u={new_user.hidden_login}&p={new_user.password}"
            print(redirect_url)
            return JsonResponse({'redirect_url': redirect_url})

    return JsonResponse({'error': 'Invalid request'}, status=400)



# Рендеринг страницы с подключением Telegram Web App SDK
async def telegram_app_view(request, hall_id):
    if request.method == 'GET':

        context = {'hall_id': hall_id}
        return render(request, 'admin_panel/telegram_app.html', context)

