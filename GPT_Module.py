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
                    "text": f"Given a URL, determine its category from the following options: News, Booking, E-commerce. Analyze the content associated with the URL: {self.url} and select the category that best matches its primary focus or content type. Respond with only the category name and nothing else."

                }
            ]
        }]

        self.identifier_payload["messages"] = message_content

    def prepare_extraction_payload(self):
        self.extractor_payload["model"] = "gpt-4-vision-preview"
        self.extractor_payload["max_tokens"] = 4096

        message_content = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """You are an advanced AI model with specialized OCR and vision capabilities, tasked with processing split images from a single webpage. Your objective is to identify the website's category (news, hotel, e-commerce, or social media) and extract all identifiable text, visual elements, and structural layout from these images. In completing this task, you must:
                            1- Accurately Piece Together Text: Ensure text that spans across images is correctly pieced together.
                            
                            2- Strict Template Adherence: Fill in all fields in the provided JSON template. Important: Do not introduce new fields beyond what the template specifies. If no data is found for a specific field, enter 'null' to maintain template integrity.

                            3- Maintain Content Hierarchy and Layout: Keep the main and side articles distinctly separated according to the webpage's actual sections, ensuring the JSON structure mirrors the webpage layout accurately.
                            
                            4- Complete and Accurate Reflection: Your analysis must capture all visible details without omissions, categorizing content exactly as displayed.

                            Adhere strictly to the provided JSON template's formatting and structure, with no deviations. It is crucial that the template is followed precisely, filling available fields with 'null' where applicable and refraining from adding any fields not explicitly listed in the template."""
                }
            ]
        }]
        self.add_images_to_payload(message_content)
        print("Template path : "+config.current_directory+"/response_templates/"+self.type+"_template.jsonl")
        self.add_template_to_payload(message_content, config.current_directory+"/response_templates/"+self.type+"_template.jsonl")

        self.extractor_payload["messages"] = message_content

    def add_images_to_payload(self, message):
        for i in range(self.image_number):
            image_path = config.current_directory+"/images/" + self.uuid + "/split_" + str(i) + ".png"
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
        
        print("Identifier Information")
        print("The tokens spent on the prompt: "+str(response_json["usage"]["prompt_tokens"]))
        print("The response tokens : "+str(response_json["usage"]["completion_tokens"]))
        print("Total tokens spent: "+str(response_json["usage"]["total_tokens"]))
 
        return message_content.strip().lower()
        

    def send_extractor_request(self):
        self.prepare_extraction_payload()
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=self.extractor_payload)
        response_json = response.json()
        message_content = response_json['choices'][0]['message']['content']

        print("Extractor Information")
        print("The tokens spent on the prompt: "+str(response_json["usage"]["prompt_tokens"]))
        print("The response tokens : "+str(response_json["usage"]["completion_tokens"]))
        print("Total tokens spent: "+str(response_json["usage"]["total_tokens"]))

        return message_content

    def run(self):
        self.type=self.send_identifier_request()
        print(self.type)
        return self.send_extractor_request()


