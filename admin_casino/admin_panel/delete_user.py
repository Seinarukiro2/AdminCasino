from models import User  # Импортируйте вашу модель
import asyncio
async def delete_user():
    user = await User.get(id=1)  # Находим пользователя с ID 1
    await user.delete()  # Удаляем пользователя
    print("Пользователь с ID 1 удален")

# asyncio.run(delete_user())