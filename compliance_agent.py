import os
import json
from groq import Groq

API_KEY = os.environ.get("GROQ_API_KEY", "......")
client = Groq(api_key=API_KEY)

def run_compliance_check(variant_key, variant_data):
    """
    Sends an ad variant to Groq (Llama-3.3-70b) to audit and align it 
    with Meta and Google Ads product policies. Returns a structured JSON.
    """
    
    system_instruction = (
        "You are an extremely strict AI Product Marketing Compliance Officer enforced with zero-tolerance policies for Business and Product advertising.\n"
        "Your absolute duty is to audit product ad variants (hook, body, cta) and modify ANY phrase that violates Meta and Google Ads policies.\n\n"
        
        "CRITICAL POLICY RULES TO ENFORCE:\n"
        "1. PERSONAL ATTRIBUTES & FLAWS (HIGH PRIORITY): Do not imply the user has a problem, financial struggle, or physical/mental deficit that your product solves. "
        "ANY phrase starting with 'Are you struggling with...', 'Tired of...', 'Don't layout your money on...' MUST BE ELIMINATED. "
        "Rewrite to focus entirely on the product's features, brand benefits, and positive outcomes.\n"
        "2. MISLEADING PRODUCT CLAIMS: Meta and Google strictly ban absolute or unprovable product outcomes. "
        "Phrases like 'The ultimate tool', 'Guaranteed to double your revenue', '100% fix for your business', or 'No more errors' MUST be softened. "
        "Use compliant, realistic language like 'Designed to optimize', 'Helps streamline', or 'An efficient solution'.\n"
        "3. AGGRESSIVE SCARCITY & PRESSURE: Remove artificial urgency commonly used in product sales (e.g., 'Buy now or lose forever', 'Last chance to save your business').\n\n"
        
        "CRITICAL PRODUCT MARKETING TEST CASES TO WATCH FOR (STRICT ENFORCEMENT):\n"
        "- The 'Pain-Point Aggression' Trap: 'Tired of losing clients because of bad software?' -> FAIL. (Focuses heavily on user's business failure). Fix: 'Streamline your client management with our automated platform.'\n"
        "- The 'Unproven ROI' Trap: 'Our product guarantees to boost your sales by 40%.' -> FAIL. (Unprovable specific metric claim). Fix: 'Designed to help businesses scale and drive revenue efficiently.'\n"
        "- The 'Before/After' State Insult: 'Stop running your business blindly.' -> FAIL. (Negative implication of the user's current ability). Fix: 'Gain clear, data-driven insights into your business operations.'\n\n"
        
        "Your output MUST strictly be a valid JSON object with these exact keys:\n"
        "- 'safe_campaign_text': { 'hook': '...', 'body': '...', 'cta': '...' }\n"
        "- 'compliance_flags': List of specific violations found (e.g., ['Personal Attributes'], ['Misleading Claims']), or ['None'] if truly flawless.\n"
        "- 'explanation_of_modifications': A detailed explanation what was changed and why it violated the product compliance policy."
    )

    user_content = f"Review this variant:\n{json.dumps(variant_data, indent=2)}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    return response.choices[0].message.content

# Test Cases: Marketing variants containing policy pitfalls
incoming_variants = {
  "variant_a": {
    "angle": "Emotional",
    "hook": "Ready to turn your AI passion into a real-world impact?",
    "body": "As a computer science student, you're likely no stranger to the thrill of exploring new technologies. But when it comes to AI and machine learning, it's not just about collecting courses - it's about bringing your ideas to life. Building AI projects and applying concepts in real-world scenarios is one of the most effective ways to develop practical machine learning skills, and to make a meaningful difference in the world.",
    "cta": "Start Building AI Projects and Unlock Your Full Potential"
  },
  "variant_b": {
    "angle": "Rational",
    "hook": "Are you missing out on the most effective way to develop practical machine learning skills?",
    "body": "Theory is essential, but it's not enough. To become job-ready and to stay ahead in the field, you need to be able to apply AI concepts in real-world scenarios. Building AI projects is the most effective way to develop practical machine learning skills, as it allows you to test your knowledge, identify areas for improvement, and develop a deeper understanding of the subject matter.",
    "cta": "Begin Applying AI Concepts in Real-World Scenarios Today"
  },
  "variant_c": {
    "angle": "Urgency",
    "hook": "The AI landscape is evolving rapidly - stay ahead by taking action now",
    "body": "As the demand for AI and machine learning expertise continues to grow, it's essential to stay ahead of the curve. Building AI projects and applying concepts in real-world scenarios is crucial to developing the practical skills you need to succeed in this field. By taking the first step today, you'll be better equipped to adapt to the changing landscape and to make the most of the opportunities that come your way.",
    "cta": "Take the First Step Towards Building Your AI Portfolio"
  }
}

final_compliant_campaign = {}

print("--- Starting Groq-Powered Compliance Checks ---\n")

for variant_key, variant_data in incoming_variants.items():
    print(f"[Analyzing via Groq] Reviewing {variant_key}...")
    
    raw_output = run_compliance_check(variant_key, variant_data)
    
    try:
        parsed_json = json.loads(raw_output)
        final_compliant_campaign[variant_key] = parsed_json
    except Exception as e:
        print(f"Error parsing JSON for {variant_key}: {e}")
        final_compliant_campaign[variant_key] = {"raw_output": raw_output}

print("\n--- Final Safe Campaign Output (JSON) ---")
print(json.dumps(final_compliant_campaign, indent=4, ensure_ascii=False))