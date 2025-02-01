from openai import OpenAI
from dotenv import load_dotenv
import base64
import json
from app.config import settings

load_dotenv()
client = OpenAI(api_key=settings.openai_api_key)

def recognize_food_from_image(image_path):
    with open(image_path, "rb") as image:
        base64_image = base64.b64encode(image.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """You are a dietitian. A user sends you an image of a meal and you tell them how many calories are in it. Use the following JSON format:

{
    "reasoning": "reasoning for the total calories",
    "food_items": [
        {
            "name": "food item name",
            "calories": "calories in the food item",
            "serving": "serving size of the food item"
        }
    ],
    "total": "total calories in the meal"
}"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "How many calories is in this meal?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            },
        ],
    )

    response_message = response.choices[0].message
    content = response_message.content

    return json.loads(content)
