# Sports, events and selections management API

## Usage

### Create a copy of .env file
```shell
cd backend/
cp .env.sample .env
cd ../
```

### Build and start backend
```shell
docker-compose up -d --build
```

### API Specification Docs - Swagger/OpenAPI
[http://localhost:8000/docs](http://localhost:8000/docs)

### Run Unit Tests
```shell
docker-compose exec server pytest -v
```

### Repository Structure
```
├── README.md
├── backend
│   ├── Dockerfile
│   ├── alembic
│   │   ├── env.py
│   │   └── versions
│   │       └── d28f489a20e9_initial.py
│   ├── alembic.ini
│   ├── app
│   │   ├── api_routes
│   │   │   ├── api.py
│   │   │   ├── deps.py
│   │   │   └── routes
│   │   │       ├── events.py
│   │   │       ├── selections.py
│   │   │       └── sports.py
│   │   ├── config
│   │   │   └── app_config.py
│   │   ├── db
│   │   │   ├── repository
│   │   │   │   ├── base.py
│   │   │   │   ├── events.py
│   │   │   │   ├── selections.py
│   │   │   │   └── sports.py
│   │   │   └── session.py
│   │   ├── main.py
│   │   └── schemas
│   │       ├── base.py
│   │       ├── event.py
│   │       ├── selection.py
│   │       └── sport.py
│   ├── poetry.lock
│   ├── pyproject.toml
│   ├── run.sh
│   └── tests
│       ├── conftest.py
│       ├── test_events.py
│       ├── test_selections.py
│       ├── test_sports.py
│       └── utils.py
└── docker-compose.yaml
```