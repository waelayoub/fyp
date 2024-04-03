import json
import base64
import config
import requests

api_key = config.api_key


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


class Gpt4:

    def __init__(self, url, uuid, image_number):
        self.url = url
        self.uuid = uuid
        self.image_number = image_number
        self.identifier_payload = {}
        self.extractor_payload = {}
        self.type = None
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
    def prepare_identification_payload(self):
        self.identifier_payload["model"] = "gpt-4-1106-preview"
        self.identifier_payload["max_tokens"] = 512
        message_content = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Which one of these 4 categories you think this website is? I want you to choose one of 
                            them only and send only the answer as the option with not additional text so is it news, 
                            booking, e-commerce or social-media? """+self.url

                }
            ]
        }]

        self.extractor_payload["messages"] = message_content

    def prepare_extraction_payload(self):
        self.extractor_payload["model"] = "gpt-4-vision-preview"
        self.extractor_payload["max_tokens"] = 4096

        message_content = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """You're an advanced AI model with specialized OCR and vision capabilities tasked with 
                    processing split images from a single webpage. Your objective is to identify the website's 
                    category (news, hotel, e-commerce, or social media) and extract all identifiable text, 
                    visual elements, and structural layout from these images. In doing so, you must: 

                    Accurately piece together text that spans across images. Capture hyperlinks, identifying them 
                    clearly with placeholder text like "[hyperlink detected]" wherever a hyperlink is present. 
                    Extract image details, including the image URL (if visible in the image) and any accompanying 
                    captions or alt text. Identify the headline categories as they appear in the image and sort 
                    articles under their respective headlines exactly as presented, without adding or assuming 
                    categories. Structure all extracted data according to the provided JSON template, filling in 
                    fields such as 'title', 'subtitle', 'images', 'links', and 'categories'. Ensure completeness and 
                    context integrity, leaving fields null where no data can be extracted. Maintain the hierarchy and 
                    layout of the webpage content in the JSON structure, keeping the main article and side articles 
                    distinctly separated and within their actual sections as per the image content. Your analysis 
                    should accurately reflect the webpage content, capturing all visible details without omission and 
                    categorizing the content exactly as it is displayed in the images. Adhere strictly to the 
                    provided JSON template formatting and structure without deviation. """
                }
            ]
        }]
        self.add_images_to_payload(message_content)

        self.add_template_to_payload(message_content, "./response_templates/news_template.jsonl")

        self.extractor_payload["messages"] = message_content

    def add_images_to_payload(self, message):
        for i in range(self.image_number):
            image_path = "./images/" + self.uuid + "/split_" + str(i) + ".png"
            base64_image = encode_image(image_path)
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

    def send_identifier_request(self):
        self.prepare_identification_payload()
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=self.identifier_payload)
        response_json = response.json()
        message_content = response_json['choices'][0]['message']['content']
        return message_content

    def send_request(self):
        self.prepare_extraction_payload()
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=self.extractor_payload)
        response_json = response.json()
        message_content = response_json['choices'][0]['message']['content']
        return message_content


tester = Gpt4("https://www.almanar.com.lb/live/", "", "")
print(tester.send_identifier_request())
