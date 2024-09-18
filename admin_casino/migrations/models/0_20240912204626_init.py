from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "project" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "project_name" VARCHAR(255) NOT NULL,
    "project_link" VARCHAR(255) NOT NULL,
    "hall_id" INT NOT NULL UNIQUE,
    "mac" VARCHAR(17) NOT NULL UNIQUE,
    "bot_token" VARCHAR(255),
    "webapp_url" VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "login" VARCHAR(100) NOT NULL UNIQUE,
    "password" VARCHAR(255) NOT NULL,
    "hidden_login" VARCHAR(100) NOT NULL,
    "hall_id" INT,
    "project_id" INT REFERENCES "project" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
