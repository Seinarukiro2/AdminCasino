from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import User, Project
import json

# Получаем список пользователей и связанных проектов
async def user_list(request):
    query = request.GET.get('q')
    hall_id_filter = request.GET.get('hall_id')

    users = await User.query.gino.all()  # Загружаем всех пользователей

    if query:
        users = [user for user in users if query.lower() in user.login.lower() or query.lower() in user.hidden_login.lower()]

    if hall_id_filter:
        users = [user for user in users if user.hall_id == int(hall_id_filter)]

    projects = await Project.query.gino.all()  # Загружаем все проекты

    return render(request, 'admin_panel/user_list.html', {
        'users': users,
        'query': query,
        'hall_id_filter': hall_id_filter,
        'projects': projects
    })

# Создаем пользователя через форму
async def create_user_form(request):
    projects = await Project.query.gino.all()  # Получаем все проекты для отображения hall_id в форме
    return render(request, 'user_form.html', {'projects': projects})

# Создаем тестового пользователя
async def create_test_user(request):
    if request.method == 'POST':
        login = request.POST.get('login')
        password = request.POST.get('password')
        hidden_login = request.POST.get('hidden_login')
        hall_id = request.POST.get('hall_id')

        project = await Project.query.where(Project.hall_id == hall_id).gino.first()
        if not project:
            return HttpResponse("Проект с таким hall_id не существует, пользователь не может быть создан", status=400)

        await User.create(
            login=login,
            password=password,
            hidden_login=hidden_login,
            project_id=project.id,
            hall_id=project.hall_id
        )

        return redirect('user_list')

    return HttpResponse("Неверный запрос", status=400)

# Список проектов
async def project_list(request):
    query = request.GET.get('q')
    hall_id_filter = request.GET.get('hall_id')

    projects = await Project.query.order_by(Project.id.desc()).gino.all()  # Получаем все проекты

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

        await Project.create(
            project_name=project_name,
            project_link=project_link,
            hall_id=hall_id,
            mac=mac
        )

        return redirect('project_list')

    return HttpResponse("Неверный запрос", status=400)

# Детали проекта и редактирование
async def project_detail(request, project_id):
    project = await Project.get(project_id)
    users = await User.query.where(User.hall_id == project.hall_id).gino.all()  # Получаем пользователей, привязанных к hall_id проекта

    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project_link = request.POST.get('project_link')
        mac = request.POST.get('mac')
        bot_token = request.POST.get('bot_token')
        webapp_url = request.POST.get('webapp_url')

        await project.update(
            project_name=project_name,
            project_link=project_link,
            mac=mac,
            bot_token=bot_token,
            webapp_url=webapp_url
        ).apply()

        return redirect('project_detail', project_id=project.id)

    return render(request, 'admin_panel/project_detail.html', {'project': project, 'users': users})

# Удаление проекта
async def delete_project(request, project_id):
    project = await Project.get(project_id)

    if request.method == 'POST':
        # Очищаем hall_id и проект для всех пользователей
        await User.update.values(hall_id=None, project_id=None).where(User.project_id == project_id).gino.status()
        await project.delete()

        return redirect('project_list')

    return render(request, 'admin_panel/project_detail.html', {'project': project})

# Проверка user_id и редирект
async def process_user_id(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('uid')

        user = await User.query.where(User.telegram_id == user_id).gino.first()

        if user:
            redirect_url = f"https://africa-slots.com/?u={user.telegram_id}&p={user.password}"
            return JsonResponse({'redirect_url': redirect_url})
        else:
            return JsonResponse({'error': 'User not found'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)

# Рендеринг страницы с подключением Telegram Web App SDK
async def telegram_app_view(request):
    return render(request, 'admin_panel/telegram_app.html')
