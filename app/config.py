import os

ENV = os.getenv("ENV")

if ENV:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"
