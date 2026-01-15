# pocket-option-bot

## Backend Setup

Prerequisites:
- Python 3

### Commands (run in terminal)
#### Initial Setup (One time required)
```
cd backend
python -m venv venv
source venv/bin/activate (linux)
./venv/Scripts/activate (windows)
pip install -r requirements.txt
cp .env.sample .env
```
Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file

#### Run Server

```
uvicorn main:app --port 8000
```

### Frontend Setup

Prerequisites:
- Node
- NPM

#### Commands (run in separate terminal)

##### Initial Setup (One time required)

```
cd frontend
npm install
```

##### Run App 

```
npm start
```

App should be running on http://localhost:3000



Use the following tutorial to get SSID for pocket option:
[How to Find Your Pocket Option SSID: Step-by-Step Guide](https://www.youtube.com/watch?v=n5YIjVmjIHw)
