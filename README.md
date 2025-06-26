# Turbo.az Car Monitor Web App

A modern web application that monitors [Turbo.az](https://turbo.az) for new car listings matching specific criteria and provides both web dashboard and Telegram notifications.

## ✨ Features

### 🌐 Web Dashboard
- **Real-time monitoring dashboard** with live updates
- **Visual car gallery** with images and details
- **Statistics and analytics** (daily, weekly, total finds)
- **Start/stop monitoring** with one click
- **Live activity log** with real-time updates
- **System testing tools** (scraper and Telegram bot)

### 📱 Telegram Integration
- **Instant notifications** with car details and images
- **Rich message formatting** with direct links
- **Optional Telegram support** (works standalone too)

### 🛡️ Smart Features
- **Duplicate detection** - never see the same car twice
- **Persistent storage** - SQLite database for car history
- **Error handling** with automatic retries
- **Responsive design** - works on all devices

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials (Optional)
```bash
cp .env.example .env
# Edit .env with your Telegram credentials (optional)
```

### 3. Launch the Web App
```bash
python run_app.py
```

### 4. Open in Browser
Navigate to **http://localhost:5000**

## 📊 Web Interface

### Dashboard
- **Statistics cards** showing total cars found, daily, and weekly counts
- **Control panel** to start/stop monitoring
- **Recent cars** with images and quick access
- **Live log** showing real-time activity
- **System tests** for configuration validation

### Cars Page
- **Complete car gallery** with pagination
- **Detailed car cards** with all information
- **Direct links** to Turbo.az listings
- **Notification status** indicators

### Settings Page
- **Configuration overview** with current settings
- **Credential setup guide** for Telegram integration
- **Search criteria** display

## 🔧 Configuration

### Search Criteria (Pre-configured)
- **Price:** 17,000 - 22,000 AZN
- **Year:** Up to 2015
- **Engine:** From 2.3L
- **Mileage:** Up to 150,000 km
- **Condition:** Used cars, including crashed and painted ones

### Telegram Setup (Optional)
1. **Get Bot Token:**
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow instructions
   - Copy the provided token

2. **Get Chat ID:**
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram
   - Copy your chat ID

3. **Configure Environment:**
   ```bash
   # .env file
   BOT_TOKEN=your_bot_token_here
   CHAT_ID=your_chat_id_here
   ```

## 🎯 Usage

### Starting Monitoring
1. Open http://localhost:5000 in your browser
2. Click **"Start Monitoring"** on the dashboard
3. Watch the live log for activity
4. New cars will appear in real-time

### Viewing Found Cars
- Check the **"Recent Cars"** section on the dashboard
- Visit the **"Cars"** page for the complete gallery
- Click **"View on Turbo.az"** to see full details

### System Testing
- Use **"Test Scraper"** to verify website connectivity
- Use **"Test Telegram"** to check bot configuration
- Monitor the live log for any issues

## 📱 Mobile Friendly

The web app is fully responsive and works great on:
- 📱 **Mobile phones** - Touch-friendly interface
- 📱 **Tablets** - Optimized layout
- 💻 **Desktops** - Full-featured experience

## 🗂️ File Structure

```
turboaz/
├── 🌐 Web App
│   ├── app.py              # Main Flask application
│   ├── run_app.py          # App launcher
│   └── templates/          # HTML templates
│       ├── base.html       # Base template
│       ├── dashboard.html  # Main dashboard
│       ├── cars.html       # Car gallery
│       └── settings.html   # Settings page
├── 🤖 Core Engine
│   ├── car_monitor.py      # Monitoring logic
│   ├── car_scraper.py      # Web scraping
│   ├── bot.py             # Telegram bot
│   └── config.py          # Configuration
├── 📁 Data & Config
│   ├── .env               # Environment variables
│   ├── app_data.db        # SQLite database (auto-created)
│   └── known_cars.txt     # Known car IDs (auto-created)
└── 📋 Setup
    ├── requirements.txt    # Dependencies
    ├── setup.py           # Setup script
    └── README.md          # This file
```

## 🔄 How It Works

1. **Web Interface:** Modern dashboard for monitoring control
2. **Scraping Engine:** Fetches car listings from Turbo.az
3. **Smart Filtering:** Only shows new cars (no duplicates)
4. **Real-time Updates:** WebSocket connection for live updates
5. **Data Storage:** SQLite database for persistence
6. **Optional Notifications:** Telegram integration for mobile alerts

## 🎨 Technology Stack

- **Backend:** Python Flask + SocketIO
- **Frontend:** Bootstrap 5 + JavaScript
- **Database:** SQLite
- **Real-time:** WebSocket connections
- **Scraping:** BeautifulSoup + Requests
- **Notifications:** Telegram Bot API

## 🚀 Deployment Options

### Local Development
```bash
python run_app.py  # Development server
```

### Production (Linux)
```bash
# Using gunicorn
pip install gunicorn
gunicorn --worker-class eventlet -w 1 app:app

# Or using systemd service (see original README)
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run_app.py"]
```

## 🆚 Modes of Operation

### 1. Web App Only
- Run the web app without Telegram
- All cars are saved to the database
- Monitor through the web interface
- Perfect for desktop monitoring

### 2. Web App + Telegram
- Full featured mode with both interfaces
- Get notifications on your phone
- Monitor through web dashboard
- Best of both worlds

### 3. Command Line (Legacy)
- Use `python main.py` for CLI-only mode
- Telegram notifications only
- No web interface
- Suitable for server deployment

## 💡 Tips

- **Leave the browser tab open** for real-time updates
- **Check the live log** to monitor system health
- **Test your setup** using the built-in test buttons
- **Bookmark the app** for quick access
- **Use mobile browser** for on-the-go monitoring

## 🔍 Troubleshooting

### App Won't Start
- Check dependencies: `pip install -r requirements.txt`
- Verify Python version: 3.7+
- Check port 5000 is available

### No Cars Found
- Use "Test Scraper" button to verify connectivity
- Check if Turbo.az website structure changed
- Monitor live log for error messages

### Telegram Not Working
- Verify credentials in .env file
- Use "Test Telegram" button
- Check bot is not blocked

### Performance Issues
- Monitor system resources
- Check internet connection
- Reduce check interval if needed

## 📄 License

This project is open source and available under the MIT License.

---

**🚗 Happy car hunting! 🏁** 