import base64
import requests
from openai import OpenAI


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
        self.payload["max_tokens"] = 1024

        message_content = [{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "You're an advanced AI model designed to process multiple split images of the same web page, leveraging advanced OCR and vision capabilities to extract comprehensive information. Your first task is to identify the type of website each set of images represents—be it news, hotel, e-commerce, or social media (Twitter/X, Facebook). After identifying the website category, your next objective is to extract all discernible text and visual elements from these images.Given that the images are parts of a larger webpage, your analysis must reconstruct the page's overall content and structure from these segments. This includes piecing together text spread across multiple images, capturing every single relevant information present.Your ultimate goal is to ensure no detail is overlooked, regardless of the website category, acknowledging the unique content each type may present. Post extraction, present the data in a comprehensive JSON format structured to reflect the diverse nature of web content. This JSON format should encompass various fields such as 'title', 'text', 'images', 'links', and 'category', with a flexible composition adaptable to the content's nature, ensuring completeness and context integrity."

                        }
                    ]
                }]

        for i in range(self.image_number):
            image_path = "./images/"+self.uuid+"/split_"+str(i)+".png"
            base64_image = self.encode_image(image_path)
            image_headers = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
            message_content[0]["content"].append(image_headers)

        self.payload["messages"] = message_content

    def send_request(self):
        self.prepare_payload()
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=self.payload)
        response_json = response.json()
        message_content = response_json['choices'][0]['message']['content']
        return message_content


