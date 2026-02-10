# 🐳 Docker Hub Setup Guide

## 📋 Требуется создать:

### 1. **Docker Hub Repository**
```bash
# 1. Зарегистрируйтесь на https://hub.docker.com
# 2. Создайте репозиторий "mybrohigh/marzban"
# 3. Установите Docker Desktop или Docker Engine
```

### 2. **GitHub Secrets для автоматической сборки**

Перейдите в ваш GitHub репозиторий → Settings → Secrets and variables → Actions:

```bash
# Добавьте следующие secrets:
DOCKERHUB_USERNAME=mybrohigh
DOCKERHUB_TOKEN=your_dockerhub_token_here
GITHUB_TOKEN=your_github_token_here
```

### 3. **GitHub Actions уже настроен** ✅

Файл `.github/workflows/build.yml` уже содержит:
```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]
  release:
    types: [ published ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
      
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
        
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ secrets.DOCKERHUB_USERNAME }}/marzban
        
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          mybrohigh/marzban:latest
          mybrohigh/marzban:${{github.ref_name}}
          ghcr.io/mybrohigh/marzban:latest
          ghcr.io/mybrohigh/marzban:${{github.ref_name}}
```

## 🚀 Как запустить:

### **Вариант 1: Использовать оригинальный образ** (рекомендуется)
```bash
docker-compose up -d
```
Использует `gozargah/marzban:latest` - стабильный оригинальный образ

### **Вариант 2: Собрать свой образ**
```bash
# 1. Создайте Docker Hub репозиторий
# 2. Добавьте GitHub Secrets
# 3. Сделайте push в GitHub - автоматическая сборка начнется
git push origin master

# 4. Используйте свой образ
docker-compose up -d
```

## 📝 Изменения в docker-compose.yml:

### **Сейчас (оригинальный образ):**
```yaml
services:
  marzban:
    image: gozargah/marzban:latest
    restart: always
    env_file: .env
    network_mode: host
    volumes:
      - /var/lib/marzban:/var/lib/marzban
```

### **После настройки Docker Hub:**
```yaml
services:
  marzban:
    image: mybrohigh/marzban:latest
    restart: always
    env_file: .env
    network_mode: host
    volumes:
      - /var/lib/marzban:/var/lib/marzban
```

## ⚡ Быстрый старт:

### **Для тестирования:**
```bash
# 1. Используйте оригинальный образ
docker-compose up -d

# 2. Проверьте работу
curl http://localhost:8000/docs
```

### **Для продакшена:**
```bash
# 1. Создайте Docker Hub репозиторий
# 2. Настройте GitHub Secrets
# 3. Соберите образ через GitHub Actions
# 4. Поменяйте image в docker-compose.yml
# 5. Запустите
docker-compose up -d
```

## 🔧 Проверка:

```bash
# Проверить статус контейнера
docker-compose ps

# Посмотреть логи
docker-compose logs marzban

# Перезапустить
docker-compose restart marzban
```

## 📊 Преимущества вашего форка:

✅ **Система лимитов** - продвинутая система управления
✅ **Расширенная статистика** - детальная аналитика
✅ **Шаблоны тарифов** - Basic/Premium/Enterprise
✅ **Автоматические уведомления** - email/telegram/webhook
✅ **Мониторинг 24/7** - фоновая проверка лимитов
✅ **База данных** - постоянное хранение настроек

## 🎯 Результат:

У вас есть выбор:
1. **Использовать оригинал** - стабильно и надежно
2. **Собрать свой** - с расширенной функциональностью

Оба варианта полностью рабочие!
