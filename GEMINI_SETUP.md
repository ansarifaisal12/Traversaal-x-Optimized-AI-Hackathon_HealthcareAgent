# Setting Up Google Gemini API for HealthGuard

This guide will help you set up Google Gemini API access for the HealthGuard application.

## Step 1: Create a Google AI Studio Account

1. Visit [Google AI Studio](https://makersuite.google.com/) and sign in with your Google account.
2. If this is your first time, follow the steps to create a Google AI Studio account.

## Step 2: Get an API Key

1. In Google AI Studio, click on your profile icon in the top-right corner.
2. Select "Get API key" from the dropdown menu.
3. If you already have API keys, they will be listed. Otherwise, click "Create API key".
4. Give your key a name (e.g., "HealthGuard") and click "Create".
5. Copy the API key value - you'll need it for the next step.

## Step 3: Configure HealthGuard to Use Gemini

1. In your HealthGuard project directory, create a file named `.env`.
2. Add the following line to your `.env` file:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```
   Replace `your_api_key_here` with the API key you copied in Step 2.

## Step 4: Install Required Packages

Ensure you have the necessary packages installed:

```bash
pip install -r requirements.txt
```

This will install the `google-generativeai` package among other dependencies.

## Step 5: Launch HealthGuard

Run the application with:

```bash
streamlit run app.py
```

HealthGuard will automatically detect your Google API key and use Gemini as the LLM provider.

## Troubleshooting

- **Rate Limits**: Google Gemini API has usage limits. If you encounter rate limit errors, wait a few minutes before trying again.
- **API Key Issues**: If the application can't connect to Gemini, verify your API key is correct and hasn't expired.
- **Model Availability**: The application uses the `gemini-pro` model. If this model becomes unavailable or is renamed, you may need to update the code.

## Switching to OpenAI

If you prefer to use OpenAI instead of (or alongside) Google Gemini:

1. Sign up for an OpenAI account and get an API key from [OpenAI Platform](https://platform.openai.com/)
2. Add your OpenAI API key to the `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

The application will prioritize Gemini if both API keys are present. 