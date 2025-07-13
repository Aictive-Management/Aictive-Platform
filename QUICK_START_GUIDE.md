# 🚀 Quick Start Guide for Aictive Platform

## 📋 What You'll Need First

You need to get API keys from these services:

### 1. Claude AI API Key (Required)
- Go to: https://console.anthropic.com
- Sign up or log in
- Go to "API Keys" section
- Click "Create Key"
- Copy the key (starts with `sk-ant-`)

### 2. Supabase (Required)
- Go to: https://app.supabase.com
- Create a free account
- Create a new project
- Go to Settings → API
- Copy:
  - `Project URL` (looks like: https://xxxxx.supabase.co)
  - `anon public` key (very long string)

### 3. Slack Webhook (Optional)
- Go to: https://api.slack.com/apps
- Create a new app
- Add "Incoming Webhooks"
- Copy the webhook URL

## 🏃‍♂️ Running the Platform

### Option 1: Easy Way (Recommended)

1. **Open Terminal**
   - Mac: Press `Cmd + Space`, type "Terminal", press Enter
   - Windows: Press `Windows + R`, type "cmd", press Enter

2. **Navigate to the project**
   ```
   cd aictive-platform
   ```

3. **Run the setup script**
   ```
   ./setup_and_run.sh
   ```

4. **Follow the prompts**
   - It will ask you to add your API keys
   - Open the `.env` file in any text editor
   - Replace the placeholder values with your real keys

5. **Access the platform**
   - Open your web browser
   - Go to: http://localhost:8000/docs
   - You'll see the API documentation!

### Option 2: Step by Step

If the script doesn't work, do this:

1. **Activate Python environment**
   ```
   source venv/bin/activate
   ```

2. **Install packages**
   ```
   pip install -r requirements.txt
   ```

3. **Edit .env file**
   - Open `.env` in a text editor
   - Add your API keys:
   ```
   ANTHROPIC_API_KEY=your_claude_key_here
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_ANON_KEY=your_supabase_key_here
   ```

4. **Run the server**
   ```
   python main_secure.py
   ```

## 🎯 Testing the API

Once running, you can test it:

### 1. Open API Documentation
- Go to: http://localhost:8000/docs
- This shows all available endpoints

### 2. Test Health Check
- Click on `GET /`
- Click "Try it out"
- Click "Execute"
- You should see a success response!

### 3. Test Email Classification (Requires Authentication)

First, you need to create an API key:

1. You'll need an admin token (for demo, we'll skip this)
2. For testing, you can modify the code temporarily

### Simple Test Without Authentication

For quick testing, open `main_secure.py` and temporarily comment out authentication:

```python
# Find this line (around line 300):
token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_CLASSIFY]))

# Change to:
# token_data: TokenData = Depends(require_scopes([Scopes.EMAIL_CLASSIFY]))
```

Then test email classification:
1. Go to `/api/classify-email` in the docs
2. Click "Try it out"
3. Use this test data:
```json
{
  "sender_email": "tenant@example.com",
  "subject": "Water leak in bathroom",
  "body_text": "There's water dripping from the ceiling in my bathroom. Please help!"
}
```
4. Click "Execute"

## 🎨 What You Should See

### Success Response:
```json
{
  "email_id": "email_1234567890_test",
  "primary_category": "maintenance",
  "confidence": 0.95,
  "keywords": ["water", "leak", "bathroom"],
  "urgency": "high",
  "sentiment": "negative",
  "processing_time": "2024-01-10T12:00:00"
}
```

### The API will:
- ✅ Classify the email as "maintenance"
- ✅ Detect high urgency
- ✅ Extract keywords
- ✅ Analyze sentiment

## 🛑 Stopping the Server

- Press `Ctrl + C` in the terminal

## 🆘 Troubleshooting

### "API key not found" error
- Make sure you saved the `.env` file after adding keys
- Restart the server after changing `.env`

### "Port already in use" error
- Another program is using port 8000
- Try: `lsof -ti:8000 | xargs kill -9`
- Then run the server again

### "Module not found" error
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt` again

## 📱 What Can This Do?

The platform can:
1. **Classify Emails** - Automatically sort into categories
2. **Analyze Maintenance Requests** - Extract repair details
3. **Generate Responses** - Create professional replies
4. **Check Compliance** - Ensure legal compliance
5. **Extract Information** - Find names, dates, amounts

## 🎉 Next Steps

1. **Test Different Emails** - Try various email types
2. **Check Slack Notifications** - If configured
3. **View API Metrics** - Check `/api/stats`
4. **Explore the Docs** - Try all endpoints

---

Need help? The error messages will guide you, or check the README.md for more details!