import json
import base64
import config
import requests

api_key = config.api_key


class Gpt4:

    def __init__(self, uuid, image_number):
        self.uuid = uuid
        self.image_number = image_number
        self.payload = {}
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def prepare_payload(self):
        self.payload["model"] = "gpt-4-vision-preview"
        self.payload["max_tokens"] = 4096

        message_content = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """You're an advanced AI model with cutting-edge OCR and vision capabilities, designed to process and analyze multiple split images from the same webpage. Your enhanced task is to accurately categorize the website type represented by each set of images—identifying it as belonging to categories such as news, hotel, e-commerce, or social media platforms (Twitter/X, Facebook).
Upon determining the category, you will focus on extracting all identifiable text and visual elements from the images. Since these images are fragments of a larger webpage, your critical challenge is to reconstruct the page's comprehensive content and layout from these pieces. This process involves meticulously joining text that spans across images and capturing every pertinent piece of information, regardless of its nature.
However, the specific requirement now is to structure the extracted data according to a predefined JSON template provided in the request. This template outlines fields such as 'title', 'text', 'images', 'links', 'category', and others tailored to accommodate the diverse and unique content found across different types of websites. While ensuring the integrity and completeness of content context, you must adapt your extraction process to fit this template, filling in each relevant field with the extracted data. For any fields where data is not available or cannot be extracted, you are instructed to leave those fields as null, ensuring the output remains clean and strictly adheres to the provided template structure.
Your primary goal is to deliver a precise and comprehensive data representation, with an emphasis on accuracy and the capability to handle various content types seamlessly, aligning with the structured requirements of the JSON template. This approach ensures that no detail is missed and that the output is both complete and formatted according to the specific data structure requested."""
                }
            ]
        }]
        self.add_images_to_payload(message_content)

        self.add_template_to_payload(message_content, "./response_templates/news_template.jsonl")

        self.payload["messages"] = message_content

    def add_images_to_payload(self, message):
        for i in range(self.image_number):
            image_path = "./images/" + self.uuid + "/split_" + str(i) + ".png"
            base64_image = self.encode_image(image_path)
            image_headers = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
            message[0]["content"].append(image_headers)

    def add_template_to_payload(self, message, template_path):
        with open(template_path, 'r') as json_file:
            json_data = json.dumps(json.load(json_file))

        json_text_header = {
            "type": "text",
            "text": json_data
        }
        message[0]["content"].append(json_text_header)

    def send_request(self):
        self.prepare_payload()
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=self.payload)
        response_json = response.json()
        message_content = response_json['choices'][0]['message']['content']
        return message_content
