# import openai

# # Use your key directly here as a test
# openai.api_key = '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'

# # Test the API
# try:
#     response = openai.Completion.create(
#         model="gpt-3.5-turbo",  # or gpt-3.5-turbo
#         prompt="Hello, how are you?",
#         max_tokens=10
#     )
#     print("Response from OpenAI:", response)

# except Exception as e:
#     print(f"An error occurred: {e}")

# from app import create_app
# import json

# def test_full_flow():
#     app = create_app()
#     client = app.test_client()
    
#     # Simulate survey submission
#     response = client.post('/api/recommend', json={
#         'mood_level': 3,
#         'stress_level': 7,
#         'sleep_hours': 5
#     })
    
#     assert response.status_code == 200
#     data = json.loads(response.data)
#     assert 'recommendations' in data
#     assert len(data['recommendations']) >= 1


import requests

url = 'http://127.0.0.1:5000/main/recommend'


sample_data = {
    "mood_level": 2,
    "stress_level": 9,
    "sleep_hours": 4,
    "energy_level": 3,
    "diet_quality": 2,
    "physical_activity": 1,
    "spent_time_with_someone": "no",
    "feelings_description": "I feel very anxious and sad today. Everything seems overwhelming."
}

response = requests.post(url, json=sample_data)

if response.status_code == 200:
    print("Recommendations:")
    print(response.json())
else:
    print("Failed:", response.status_code)
