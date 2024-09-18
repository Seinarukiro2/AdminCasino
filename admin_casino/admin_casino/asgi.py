import os
from django.core.asgi import get_asgi_application
from tortoise import Tortoise
from starlette.applications import Starlette

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_casino.settings')

# Конфигурация Tortoise ORM
TORTOISE_ORM = {
    "connections": {
        "default": "postgres://admin_dev:CasinoAdminDev4464@localhost:5432/admin_casino"
    },
    "apps": {
        "models": {
            "models": ["admin_panel.models", "aerich.models"],  # Укажите свои модели и aerich
            "default_connection": "default",
        },
    },
}

# Инициализация Tortoise ORM
async def init_tortoise():
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas(safe=True)  # Генерация схем, если они не существуют
        print("Tortoise ORM успешно инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации Tortoise ORM: {e}")

# Жизненный цикл приложения
async def lifespan(app):
    print("Инициализация Tortoise ORM при запуске приложения")
    await init_tortoise()
    yield
    print("Закрытие соединения с базой данных")
    await Tortoise.close_connections()

# Получаем стандартное ASGI-приложение Django
django_app = get_asgi_application()

# Создаем Starlette-приложение с жизненным циклом и интеграцией Django
app = Starlette(lifespan=lifespan)
app.mount("/", django_app)

# Экспортируем приложение для Uvicorn
application = app
