from ImageCaptureModule import ImageCaptureModule
from GPT_Module import Gpt4


class ScraperEngine:

    def __init__(self, start_url):
        self.start_url = start_url
        self.image_module = None
        self.website_image_information = None
        self.ai_module = None

    def get_images(self):
        self.image_module = ImageCaptureModule(self.start_url)
        self.website_image_information = self.image_module.run()

    def initiate_ai(self):
        self.ai_module = Gpt4(self.website_image_information[0], self.website_image_information[1])

    def send_request(self):
        return self.ai_module.send_request()

    def run(self):
        self.get_images()
        input("Press enter to continue")
        self.initiate_ai()
        print(self.send_request())


url = input("Insert the wanted url: ")
scraper = ScraperEngine(url)
scraper.run()

