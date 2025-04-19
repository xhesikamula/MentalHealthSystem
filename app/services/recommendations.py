import openai
import json
from flask import current_app
from datetime import datetime

def analyze_survey_data(survey_data):
    """Enhanced analysis of survey data with additional insights"""
    analysis = {
        'key_concerns': [],
        'strengths': [],
        'mood_profile': '',
        'stress_profile': '',
        'energy_analysis': '',
        'sleep_quality': '',
        'lifestyle_factors': []
    }
    
    # Mood analysis (enhanced)
    mood = survey_data.get('mood_level', 5)
    if mood < 3:
        analysis['key_concerns'].append('severe low mood')
        analysis['mood_profile'] = 'very low'
    elif mood < 5:
        analysis['key_concerns'].append('low mood')
        analysis['mood_profile'] = 'low'
    elif mood > 8:
        analysis['strengths'].append('positive mood')
        analysis['mood_profile'] = 'high'
    else:
        analysis['mood_profile'] = 'stable'

    # Stress analysis (enhanced)
    stress = survey_data.get('stress_level', 5)
    if stress > 8:
        analysis['key_concerns'].append('very high stress')
        analysis['stress_profile'] = 'very high'
    elif stress > 6:
        analysis['key_concerns'].append('high stress')
        analysis['stress_profile'] = 'high'
    elif stress < 3:
        analysis['strengths'].append('low stress')
        analysis['stress_profile'] = 'low'
    else:
        analysis['stress_profile'] = 'moderate'

    # Energy analysis (enhanced)
    energy = survey_data.get('energy_level', 5)
    if energy < 3:
        analysis['key_concerns'].append('severe fatigue')
        analysis['energy_analysis'] = 'very low'
    elif energy < 5:
        analysis['key_concerns'].append('low energy')
        analysis['energy_analysis'] = 'low'
    elif energy > 7:
        analysis['strengths'].append('high energy')
        analysis['energy_analysis'] = 'high'
    else:
        analysis['energy_analysis'] = 'balanced'

    # Sleep analysis (new)
    sleep = survey_data.get('sleep_hours', 8)
    if sleep < 5:
        analysis['key_concerns'].append('severe sleep deprivation')
        analysis['sleep_quality'] = 'very poor'
    elif sleep < 7:
        analysis['key_concerns'].append('insufficient sleep')
        analysis['sleep_quality'] = 'poor'
    elif sleep > 9:
        analysis['lifestyle_factors'].append('excessive sleep')
        analysis['sleep_quality'] = 'excessive'
    else:
        analysis['strengths'].append('adequate sleep')
        analysis['sleep_quality'] = 'good'

    # Lifestyle factors (enhanced)
    if survey_data.get('diet_quality', 5) < 4:
        analysis['key_concerns'].append('poor nutrition')
    elif survey_data.get('diet_quality', 5) > 7:
        analysis['strengths'].append('good nutrition')
        
    if survey_data.get('physical_activity', 0) < 2:
        analysis['key_concerns'].append('very sedentary')
    elif survey_data.get('physical_activity', 0) > 6:
        analysis['strengths'].append('active lifestyle')
        
    if survey_data.get('spent_time_with_someone') == 'no':
        analysis['lifestyle_factors'].append('no social contact today')
    else:
        analysis['strengths'].append('social interaction today')

    return analysis

def generate_ai_recommendations(survey_data):
    """Generate comprehensive recommendations using OpenAI with enhanced analysis"""
    try:
        analysis = analyze_survey_data(survey_data)
        prompt = build_ai_prompt(analysis, survey_data)
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": """You're a compassionate mental health advisor. Provide:
                    1. 3-5 prioritized recommendations
                    2. Each with clear rationale
                    3. Practical implementation steps
                    4. Categorized by urgency"""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=350
        )
        
        content = response.choices[0].message.content
        return format_ai_response(content, analysis)
        
    except Exception as e:
        current_app.logger.error(f"OpenAI error: {str(e)}")
        return generate_fallback_recommendations(survey_data)

def build_ai_prompt(analysis, survey_data):
    """Construct a detailed, structured prompt for AI analysis"""
    return f"""
    **Comprehensive Mental Health Analysis Request**
    
    User Profile:
    - Mood: {survey_data['mood_level']}/10 ({analysis['mood_profile']})
    - Stress: {survey_data['stress_level']}/10 ({analysis['stress_profile']})
    - Energy: {survey_data['energy_level']}/10 ({analysis['energy_analysis']})
    - Sleep: {survey_data['sleep_hours']} hrs ({analysis['sleep_quality']})
    - Diet: {survey_data['diet_quality']}/10
    - Activity: {survey_data['physical_activity']}/10
    - Social: {'Yes' if survey_data['spent_time_with_someone'] == 'yes' else 'No'}
    - Feelings: "{survey_data['feelings_description']}"

    Key Concerns: {', '.join(analysis['key_concerns']) or 'None'}
    Strengths: {', '.join(analysis['strengths']) or 'None'}
    Lifestyle Factors: {', '.join(analysis['lifestyle_factors']) or 'None'}

    Please provide recommendations that:
    1. Address immediate concerns (if any)
    2. Build on existing strengths
    3. Include specific actions
    4. Provide scientific rationale
    5. Suggest implementation timing

    Format as JSON with:
    - "priority" (high/medium/low)
    - "category"
    - "recommendation"
    - "rationale"
    - "when_to_implement"
    """

def format_ai_response(content, analysis):
    """Convert AI response to structured format with fallback handling"""
    try:
        # Try to extract JSON
        if '{' in content and '}' in content:
            json_str = content.split('{', 1)[1].rsplit('}', 1)[0]
            return [json.loads('{' + json_str + '}')]
        
        # Fallback to text processing
        recommendations = []
        for line in content.split('\n'):
            if line.strip() and '•' in line:
                parts = line.split('•', 1)[1].split('(', 1)
                rec_text = parts[0].strip()
                rationale = parts[1].replace(')', '').strip() if len(parts) > 1 else ''
                recommendations.append({
                    "category": "General",
                    "text": rec_text,
                    "rationale": rationale or "Suggested by AI",
                    "priority": "medium"
                })
        return recommendations or generate_fallback_recommendations(analysis)
    
    except Exception as e:
        current_app.logger.error(f"Response formatting error: {str(e)}")
        return generate_fallback_recommendations(analysis)

def generate_fallback_recommendations(survey_data):
    """Enhanced rule-based fallback recommendations"""
    recommendations = []
    analysis = analyze_survey_data(survey_data)
    
    # Mood recommendations
    if 'severe low mood' in analysis['key_concerns']:
        recommendations.append({
            "category": "Mood Emergency",
            "text": "Contact a mental health professional immediately",
            "rationale": "Severely low mood requires professional support",
            "priority": "high"
        })
    elif 'low mood' in analysis['key_concerns']:
        recommendations.append({
            "category": "Mood Boost",
            "text": "Try a 10-minute walk in sunlight",
            "rationale": "Sunlight increases serotonin levels",
            "priority": "medium"
        })
    
    # Stress recommendations
    if 'very high stress' in analysis['key_concerns']:
        recommendations.extend([
            {
                "category": "Stress Relief",
                "text": "Practice 4-7-8 breathing (inhale 4s, hold 7s, exhale 8s)",
                "rationale": "Activates parasympathetic nervous system",
                "priority": "high"
            },
            {
                "category": "Stress Relief",
                "text": "Write down your stressors for 5 minutes",
                "rationale": "Externalization reduces cognitive load",
                "priority": "medium"
            }
        ])
    
    # Sleep recommendations
    if 'severe sleep deprivation' in analysis['key_concerns']:
        recommendations.append({
            "category": "Sleep Priority",
            "text": "Aim for 7-9 hours sleep tonight with no screens 1 hour before bed",
            "rationale": "Chronic sleep deprivation impairs cognitive function",
            "priority": "high"
        })
    
    # Ensure at least 3 recommendations
    if len(recommendations) < 3:
        recommendations.extend([
            {
                "category": "General Wellness",
                "text": "Drink a glass of water",
                "rationale": "Hydration improves cognitive function",
                "priority": "low"
            },
            {
                "category": "General Wellness",
                "text": "Stretch for 2 minutes",
                "rationale": "Improves circulation and reduces stiffness",
                "priority": "low"
            }
        ])
    
    return recommendations[:5]  # Return max 5 recommendations