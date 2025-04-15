import openai
from flask import current_app
from datetime import datetime

def analyze_survey_data(survey_data):
    """Perform initial analysis of survey data to identify key patterns"""
    analysis = {
        'key_concerns': [],
        'mood_profile': '',
        'stress_profile': '',
        'energy_analysis': '',
        'lifestyle_factors': []
    }
    
    # Mood analysis
    mood = survey_data.get('mood_level', 5)
    if mood < 4:
        analysis['key_concerns'].append('low mood')
        analysis['mood_profile'] = 'low'
    elif mood > 7:
        analysis['mood_profile'] = 'elevated'
    else:
        analysis['mood_profile'] = 'neutral'

    # Stress analysis
    stress = survey_data.get('stress_level', 5)
    if stress > 6:
        analysis['key_concerns'].append('high stress')
        analysis['stress_profile'] = 'high'
    elif stress < 4:
        analysis['stress_profile'] = 'low'
    else:
        analysis['stress_profile'] = 'moderate'

    # Energy analysis
    energy = survey_data.get('energy_level', 5)
    if energy < 4:
        analysis['key_concerns'].append('low energy')
        analysis['energy_analysis'] = 'fatigued'
    elif energy > 7:
        analysis['energy_analysis'] = 'high energy'
    else:
        analysis['energy_analysis'] = 'balanced'

    # Lifestyle factors
    if survey_data.get('sleep_hours', 8) < 7:
        analysis['lifestyle_factors'].append('sleep deprivation')
    if survey_data.get('diet_quality', 5) < 5:
        analysis['lifestyle_factors'].append('suboptimal nutrition')
    if survey_data.get('physical_activity', 0) < 3:
        analysis['lifestyle_factors'].append('sedentary lifestyle')
    if survey_data.get('spent_time_with_someone') == 'no':
        analysis['lifestyle_factors'].append('social isolation')

    return analysis

def generate_recommendations(survey_data):
    """Generate recommendations with MySQL-compatible formatting"""
    try:
        # Simple rule-based recommendations (no API calls)
        recommendations = []
        
        # Mood-based recommendations
        if survey_data['mood_level'] < 4:
            recommendations.append({
                'category': 'Mood Boost',
                'text': 'Listen to uplifting music for 15 minutes',
                'rationale': 'Music therapy can improve low mood states'
            })
        elif survey_data['mood_level'] > 7:
            recommendations.append({
                'category': 'Mood Regulation',
                'text': 'Practice mindfulness meditation',
                'rationale': 'Helps maintain balanced emotional states'
            })
        
        # Stress-based recommendations
        if survey_data['stress_level'] > 6:
            recommendations.append({
                'category': 'Stress Relief',
                'text': 'Try progressive muscle relaxation',
                'rationale': 'Reduces physical tension from stress'
            })
        
        # Sleep-based recommendations
        if survey_data['sleep_hours'] < 7:
            recommendations.append({
                'category': 'Sleep Hygiene',
                'text': 'Establish a consistent bedtime routine',
                'rationale': 'Regular sleep schedule improves sleep quality'
            })
        
        # Social recommendations
        if survey_data['spent_time_with_someone'] == 'no':
            recommendations.append({
                'category': 'Social Connection',
                'text': 'Reach out to a friend or family member',
                'rationale': 'Social support improves mental wellbeing'
            })
        
        # Fallback if no specific recommendations
        if not recommendations:
            recommendations.append({
                'category': 'General Wellness',
                'text': 'Take a 10-minute walk outside',
                'rationale': 'Physical activity and nature exposure boost wellbeing'
            })
        
        return recommendations
        
    except Exception as e:
        current_app.logger.error(f"Recommendation generation error: {str(e)}")
        return [{
            'category': 'General',
            'text': 'Practice deep breathing for 5 minutes',
            'rationale': 'Helps reduce stress and anxiety'
        }]
    
def build_ai_prompt(analysis, survey_data):
    """Build a detailed prompt for AI recommendations"""
    prompt = f"""
    User Mental Health Profile:
    - Mood: {survey_data.get('mood_level', 5)}/10 ({analysis['mood_profile']})
    - Stress: {survey_data.get('stress_level', 5)}/10 ({analysis['stress_profile']})
    - Energy: {survey_data.get('energy_level', 5)}/10 ({analysis['energy_analysis']})
    - Sleep: {survey_data.get('sleep_hours', 8)} hours
    - Diet Quality: {survey_data.get('diet_quality', 5)}/10
    - Physical Activity: {survey_data.get('physical_activity', 0)}/10
    - Social Contact: {'Yes' if survey_data.get('spent_time_with_someone') == 'yes' else 'No'}
    - Current Feelings: "{survey_data.get('feelings_description', 'not specified')}"

    Key Concerns: {', '.join(analysis['key_concerns']) or 'none'}
    Lifestyle Factors: {', '.join(analysis['lifestyle_factors']) or 'none'}

    Please provide 5-7 specific, personalized recommendations that:
    1. Address the key concerns
    2. Consider all provided factors
    3. Include at least one physical, one mental, and one social suggestion
    4. Provide practical actions the user can take today
    5. Include brief explanations for each recommendation

    Format each recommendation as:
    • [Category] Recommendation (Brief rationale)
    """
    return prompt