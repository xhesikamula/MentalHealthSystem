import openai

# Use your key directly here as a test
openai.api_key = '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'

# Test the API
try:
    response = openai.Completion.create(
        model="gpt-3.5-turbo",  # or gpt-3.5-turbo
        prompt="Hello, how are you?",
        max_tokens=10
    )
    print("Response from OpenAI:", response)

except Exception as e:
    print(f"An error occurred: {e}")
