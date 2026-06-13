# from core.config.secret import Secrets

# print(Secrets.APP_ENV)
# print(Secrets.DATABASE_HOST)


from core.config.settings import settings

print(settings.project_root)

print(settings.database_url)

print(settings.raw_data_dir)

