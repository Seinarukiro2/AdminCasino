import os
from django.core.asgi import get_asgi_application
from admin_panel.models import db  # Gino ORM
from starlette.applications import Starlette

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_casino.settings')

# Получаем стандартное ASGI-приложение Django
django_app = get_asgi_application()

# Инициализация Gino
async def init_gino():
    try:
        await db.set_bind('postgresql+asyncpg://admin_dev:CasinoAdminDev4464@localhost:5432/admin_casino')
        print("Gino успешно инициализировано")
    except Exception as e:
        print(f"Ошибка при инициализации Gino: {e}")

# Жизненный цикл приложения
async def lifespan(app):
    print("Инициализация Gino при запуске приложения")
    await init_gino()
    yield
    print("Закрытие соединения с базой данных")
    await db.pop_bind().close()

# Создаем Starlette-приложение с жизненным циклом и интеграцией Django
app = Starlette(lifespan=lifespan)
app.mount("/", django_app)

# Экспортируем приложение для Uvicorn
application = app
