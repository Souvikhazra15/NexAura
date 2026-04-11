from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import requests
import json
from datetime import datetime, timedelta
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import threading

token: Final[str] = TOKEN

bot_username: Final[str] = '@anamolyalert_bot'
BACKEND_URL: Final[str] = 'http://localhost:8000'

# Store user subscriptions and alert streaming status
user_subscriptions = {}  # {user_id: {'subscribed': bool, 'alerts': set()}}
last_alert_check = {}
bot_alert_streaming = True  # Global flag to control alert fetching

#Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.chat.id
    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = {'subscribed': True, 'alerts': set()}
    else:
        user_subscriptions[user_id]['subscribed'] = True
    
    await update.message.reply_text(
        '🚨 Welcome to Anomaly Alert Bot!\n\n'
        'I will notify you about anomalies detected in your IoT devices.\n\n'
        'Commands:\n'
        '/start - Start receiving alerts\n'
        '/stop - Stop receiving alerts\n'
        '/alerts - View current alerts\n'
        '/subscribe - Subscribe to alerts\n'
        '/unsubscribe - Unsubscribe from alerts\n'
        '/help - Get help'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '📚 Help Guide\n\n'
        'Commands:\n'
        '• /start - Activate alert notifications\n'
        '• /stop - Deactivate alert notifications\n'
        '• /subscribe - Subscribe to get alerts\n'
        '• /unsubscribe - Unsubscribe from alerts\n'
        '• /alerts - View recent alerts\n'
        '• /custom - Custom command\n\n'
        'Alert types:\n'
        '🔴 Critical: Threshold exceeded by ±3σ\n'
        '🟡 Warning: Threshold exceeded by ±2σ\n\n'
        'Use /alerts to check current anomalies in your system.'
    )

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.chat.id
    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = {'subscribed': True, 'alerts': set()}
    else:
        user_subscriptions[user_id]['subscribed'] = True
    
    await update.message.reply_text('✅ You are now subscribed to anomaly alerts!')

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.chat.id
    if user_id in user_subscriptions:
        user_subscriptions[user_id]['subscribed'] = False
    
    await update.message.reply_text('❌ You have unsubscribed from anomaly alerts.')

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.chat.id
    if user_id in user_subscriptions:
        user_subscriptions[user_id]['subscribed'] = False
    
    await update.message.reply_text('⏸️ Alert notifications have been stopped.')

async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('🔄 Fetching current alerts...')
    
    try:
        # Fetch alerts from backend
        response = requests.get(f'{BACKEND_URL}/api/anomalies', timeout=5)
        if response.status_code == 200:
            data = response.json()
            anomalies = data.get('anomalies', [])
            
            if not anomalies:
                await update.message.reply_text('✅ No anomalies detected. System is healthy!')
                return
            
            # Group by severity
            critical_alerts = [a for a in anomalies if a.get('severity') == 'critical']
            warning_alerts = [a for a in anomalies if a.get('severity') == 'warning']
            
            message = f'📊 Alert Summary\n\n'
            message += f'🔴 Critical: {len(critical_alerts)}\n'
            message += f'🟡 Warning: {len(warning_alerts)}\n'
            message += f'📈 Total: {len(anomalies)}\n\n'
            
            # Show top 5 critical alerts
            if critical_alerts:
                message += '🔴 Critical Alerts:\n'
                for alert in critical_alerts[:5]:
                    signal = alert.get('signal', 'Unknown')
                    value = alert.get('value', 'N/A')
                    threshold = alert.get('threshold', 'N/A')
                    message += f'  • {signal}: {value} (threshold: {threshold})\n'
                
                if len(critical_alerts) > 5:
                    message += f'  ... and {len(critical_alerts) - 5} more\n'
            
            # Show top 3 warning alerts
            if warning_alerts:
                message += '\n🟡 Warning Alerts:\n'
                for alert in warning_alerts[:3]:
                    signal = alert.get('signal', 'Unknown')
                    value = alert.get('value', 'N/A')
                    message += f'  • {signal}: {value}\n'
                
                if len(warning_alerts) > 3:
                    message += f'  ... and {len(warning_alerts) - 3} more\n'
            
            await update.message.reply_text(message)
        else:
            await update.message.reply_text('❌ Failed to fetch alerts from system.')
    
    except Exception as e:
        print(f'Error fetching alerts: {e}')
        await update.message.reply_text(f'❌ Error: {str(e)}')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('This is a custom command.')

# Helper functions for alert management
def format_alert_message(alert: dict) -> str:
    """Format a single alert for Telegram display"""
    signal = alert.get('signal', 'Unknown Signal')
    severity = alert.get('severity', 'unknown').upper()
    value = alert.get('value', 'N/A')
    threshold = alert.get('threshold', 'N/A')
    message = alert.get('message', 'Anomaly detected')
    action = alert.get('suggested_action', 'Please investigate')
    timestamp = alert.get('timestamp', '')
    
    severity_icon = '🔴' if severity == 'CRITICAL' else '🟡'
    
    formatted = (
        f'{severity_icon} {severity} ALERT\n'
        f'Signal: {signal}\n'
        f'Value: {value}\n'
        f'Threshold: {threshold}\n'
        f'Message: {message}\n'
        f'Action: {action}\n'
    )
    
    if timestamp:
        formatted += f'Time: {timestamp}\n'
    
    return formatted

async def fetch_and_send_alerts(application: Application, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch alerts from backend and send to subscribed users"""
    global bot_alert_streaming
    
    # Only fetch alerts if streaming is active
    if not bot_alert_streaming:
        return
    
    try:
        response = requests.get(f'{BACKEND_URL}/api/anomalies', timeout=5)
        if response.status_code == 200:
            data = response.json()
            anomalies = data.get('anomalies', [])
            
            if not anomalies:
                return
            
            # For each subscribed user
            for user_id, sub_info in user_subscriptions.items():
                if not sub_info.get('subscribed', False):
                    continue
                
                # Check for new alerts
                current_alert_ids = set(str(a.get('id', '')) for a in anomalies)
                previous_alert_ids = sub_info.get('alerts', set())
                
                new_alerts = []
                for alert in anomalies:
                    alert_id = str(alert.get('id', ''))
                    if alert_id not in previous_alert_ids and alert.get('severity') in ['critical', 'warning']:
                        new_alerts.append(alert)
                
                # Send new alerts
                for alert in new_alerts:
                    try:
                        message_text = format_alert_message(alert)
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=f'⚠️ NEW ALERT\n\n{message_text}',
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        print(f'Failed to send alert to user {user_id}: {e}')
                
                # Update tracked alerts
                user_subscriptions[user_id]['alerts'] = current_alert_ids
    
    except Exception as e:
        print(f'Error fetching alerts: {e}')

#Responses
def handle_response(text: str) -> str: 
    processed: str = text.lower()
    if 'hello' in processed:
        return 'Hello! How can I assist you today?'
    elif 'help' in processed:
        return 'I am here to help you monitor your IoT devices for any anomalies. I will send you alerts whenever an anomaly is detected. You can use the /start command to start receiving alerts and the /help command to see this message again.'
    else:
        return 'I am sorry, I did not understand that. Please use the /help command for assistance.'

#Message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type} sent: {text}')

    if message_type == 'group':
        if bot_username in text:
            new_text: str = text.replace(bot_username, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)

    print(f'Bot response: {response}')
    await update.message.reply_text(response)



async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f'Update {update} caused error {context.error}')

# FastAPI endpoints for controlling bot alerts
def create_fastapi_app(app: Application):
    """Create a FastAPI app to handle bot control requests"""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    
    fastapi_app = FastAPI()
    
    @fastapi_app.post("/api/bot/stop")
    async def bot_stop():
        """Stop bot from sending alerts"""
        global bot_alert_streaming
        bot_alert_streaming = False
        print("Bot alert streaming disabled")
        return JSONResponse({"status": "stopped", "message": "Bot alert fetching paused"})
    
    @fastapi_app.post("/api/bot/start")
    async def bot_start():
        """Start bot to send alerts"""
        global bot_alert_streaming
        bot_alert_streaming = True
        print("Bot alert streaming enabled")
        return JSONResponse({"status": "started", "message": "Bot alert fetching resumed"})
    
    @fastapi_app.get("/api/bot/status")
    async def bot_status():
        """Get bot streaming status"""
        global bot_alert_streaming
        return JSONResponse({"streaming": bot_alert_streaming})
    
    @fastapi_app.post("/api/bot/send-alert")
    async def send_alert_to_users(request: Request):
        """Send formatted alert to subscribed users with parameter breakdown"""
        try:
            body = await request.json()
            message_type = body.get('message_type', 'main')
            data = body.get('data', {})
            
            # Format message based on type
            if message_type == 'main':
                severity = data.get('severity', '').upper()
                message = data.get('message', '')
                timestamp = data.get('timestamp', '')
                severity_icon = '🔴' if severity == 'CRITICAL' else '🟡'
                alert_text = f'{severity_icon} {severity} ALERT\n{message}\nTime: {timestamp}'
            
            elif message_type == 'signal':
                signal = data.get('signal', 'Unknown')
                value = data.get('value', 'N/A')
                alert_type = data.get('type', 'Unknown')
                alert_text = f'📊 SIGNAL DETAILS\nSignal: {signal}\nValue: {value}\nType: {alert_type}'
            
            elif message_type == 'signals':
                contributing = data.get('contributing_signals', [])
                alert_text = '📈 CONTRIBUTING SIGNALS\n'
                for sig in contributing[:5]:  # Show top 5
                    importance = sig.get('importance', 0)
                    alert_text += f'  • {sig.get("signal")}: {int(importance*100)}% importance\n'
            
            elif message_type == 'action':
                action = data.get('suggested_action', 'Please investigate')
                score = data.get('score', 0)
                alert_text = f'⚡ RECOMMENDED ACTION\nScore: {int(score*100)}%\nAction: {action}'
            
            else:
                alert_text = str(data)
            
            # Send to all subscribed users
            user_count = 0
            for user_id, sub_info in user_subscriptions.items():
                if not sub_info.get('subscribed', False):
                    continue
                
                try:
                    await app.bot.send_message(
                        chat_id=user_id,
                        text=alert_text,
                        parse_mode='HTML'
                    )
                    user_count += 1
                except Exception as e:
                    print(f'Failed to send to user {user_id}: {e}')
            
            print(f'📤 Bot sent {message_type} alert to {user_count} users')
            return JSONResponse({"status": "sent", "type": message_type, "users": user_count})
        
        except Exception as e:
            print(f'Error sending alert: {e}')
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    
    return fastapi_app


if __name__ == '__main__':
    print('Starting bot...')
    
    # Create Telegram application
    application = Application.builder().token(token).build()
    
    #Commands
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('custom', custom_command))
    application.add_handler(CommandHandler('subscribe', subscribe_command))
    application.add_handler(CommandHandler('unsubscribe', unsubscribe_command))
    application.add_handler(CommandHandler('stop', stop_command))
    application.add_handler(CommandHandler('alerts', alerts_command))

    #Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    #Errors
    application.add_error_handler(error)
    
    # Add periodic alert checking (every 5 seconds)
    if application.job_queue is not None:
        application.job_queue.run_repeating(
            lambda context: fetch_and_send_alerts(application, context),
            interval=5,
            first=0
        )
    else:
        print('Warning: JobQueue not available')

    # Create and run FastAPI app in a separate thread
    import uvicorn
    from fastapi import FastAPI
    
    fastapi_app = create_fastapi_app(application)
    
    def run_fastapi():
        """Run FastAPI server on port 3001"""
        uvicorn.run(fastapi_app, host="0.0.0.0", port=3001, log_level="error")
    
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    print('FastAPI control server started on port 3001')

    print('Bot is running...')
    application.run_polling(poll_interval=3)
  