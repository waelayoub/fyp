import time
import os
from PIL import Image
from playwright.sync_api import sync_playwright
import uuid


class ImageCaptureModule:

    def __init__(self, start_url):
        self.uuid = None
        self.splits = None

        self.playwright = sync_playwright().start()
        browser_type = self.playwright.chromium
        self.context = browser_type.launch_persistent_context("", headless=False, args=[
            f'--load-extension=./fihnjjcciajhdojfnbdddfaoknhalnja/3.5.0_0',
            f'--disable-extensions-except=./fihnjjcciajhdojfnbdddfaoknhalnja/3.5.0_0'
        ])

        if len(self.context.background_pages) == 0:
            background_page = self.context.wait_for_event('backgroundpage')
        else:
            background_page = self.context.background_pages[0]
        self.page = self.context.new_page()
        self.start_url = start_url

    def run(self):
        output_directory = "./images"
        self.crawl_and_capture(output_directory)
        self.context.close()
        # Stop Playwright explicitly to clean up resources
        self.playwright.stop()
        return [self.uuid, self.splits]

    def wait_for_images_to_load(self, timeout=30000):
        js_check_images = """
        () => {
            return Array.from(document.images).every((img) => img.complete);
        }
        """
        self.page.wait_for_function(js_check_images, timeout=timeout)

    def get_dimensions(self):
        inner_h = """
        () => {
            return window.innerHeight;
        }
        """

        b_scroll_h = """
        () => {
            return document.documentElement.scrollHeight;
        }
        """

        body_height = self.page.evaluate(b_scroll_h)
        window_height = self.page.evaluate(inner_h)
        return body_height, window_height

    def scroll_to_top(self):
        js_scroll_back_to_the_top = """
        () => {
            window.scrollTo(0, 0);
        }
        """
        self.page.evaluate(js_scroll_back_to_the_top)

    def scroll_and_wait_for_images(self, timeout=30000):

        body_height, window_height = self.get_dimensions()
        scroller_number = round(body_height/window_height)
        if scroller_number > 8:
            scroller_number = 8

        js_scroll = """
        () => {
            window.scrollBy(0, window.innerHeight);
        }
        """

        try:
            self.wait_for_images_to_load(timeout)
        except Exception as e:
            if not (str(e).__contains__("EvalError")):
                print(e)
                print("Crawling will start even if some images has not been loaded")
                timeout = 3000
            else:
                time.sleep(1)

        for i in range(scroller_number):
            self.page.evaluate(js_scroll)
            time.sleep(4)
            try:
                self.wait_for_images_to_load(timeout)
            except Exception as e:
                if not (str(e).__contains__("EvalError")):
                    print("Continuing crawling even with not all loaded images")
                else:
                    time.sleep(1)
            print("Completion: "+str(round((i+1)/scroller_number*100, 2))+" %")
        self.scroll_to_top()

    def crawl_and_capture(self, base_output_path, site_timeout=90000):
        try:
            self.page.goto(self.start_url, wait_until='networkidle', timeout=site_timeout)
        except Exception as e:
            print(f"An error occurred while processing {self.start_url}: {e}")
        finally:
            if input("Want to remove cookies?").strip().lower() == "yes":
                self.remove_disclaimer_cookies()
            if input("Want to remove advertisements?").strip().lower() == "yes":
                self.remove_ads()

            self.scroll_and_wait_for_images(site_timeout)
            self.uuid = str(uuid.uuid4())
            folder_path = base_output_path+"/"+self.uuid

            os.mkdir(path=folder_path)

            filename = "full_page.png"
            output_path = f"{folder_path}/{filename}"

            time.sleep(3)
            self.page.screenshot(path=output_path, full_page=True, animations="allow")
            print(f"Screenshot saved for {self.start_url} at {output_path}")
            self.crop_image(output_path)
            print("\n\n")
            self.split_image(output_path, folder_path, split_height=1024, image_format='png')
            self.page.close()

    def crop_image(self, input_path):
        with Image.open(input_path) as img:
            img_width, img_height = img.size
            if img_height > 5120:
                img.crop()
                new_image = img.crop((0, 0, img_width, 5120))
                new_image.save(input_path)

    def split_image(self, input_path, output_directory, split_height=1024, image_format='png'):
        """
        Split the input image into multiple smaller images of a specified height.

        Args:
        - input_path (str): The path of the input image to split.
        - output_directory (str): The directory where the split images will be saved.
        - split_height (int): The height of each split image.
        - image_format (str): The format of the split images.
        """
        with Image.open(input_path) as img:
            img_width, img_height = img.size

            # Calculate the number of splits needed based on the split height
            self.splits = img_height // split_height
            if img_height % split_height != 0:
                self.splits += 1

            # Split the image and save each part
            for i in range(self.splits):
                top = i * split_height
                bottom = min((i + 1) * split_height, img_height)

                # Crop the image
                img_cropped = img.crop((0, top, img_width, bottom))
                split_filename = os.path.join(output_directory, f"split_{i}.{image_format}")

                # Save the cropped image
                img_cropped.save(split_filename)
                # print(f"Saved split image: {split_filename}")

    def remove_disclaimer_cookies(self):
        generic_cookie_js = """
            const selectors = [
                'cookie', 'consent', 'gdpr', 'disclaimer', 'privacy', 'popup', 'overlay',
                'notice', 'banner', 'policy', 'compliance', 'WebsiteCookies'
            ];
            selectors.forEach(selector => {
                document.querySelectorAll(`[id*="${selector}"], [class*="${selector}"]`).forEach(element => {
                    element.remove();
                });
            });
        """

        generic_cookie_css = """
            [id*='cookie'], [class*='cookie'],
            [id*='consent'], [class*='consent'],
            [id*='gdpr'], [class*='gdpr'],
            [id*='disclaimer'], [class*='disclaimer'],
            [id*='privacy'], [class*='privacy'],
            [id*='popup'], [class*='popup'],
            [id*='overlay'], [class*='overlay'],
            [id*='notice'], [class*='notice'],
            [id*='banner'], [class*='banner'],
            [id*='policy'], [class*='policy'],
            [id*='compliance'], [class*='compliance'] {
                display: none !important;
            }
        """
        self.page.evaluate(generic_cookie_js)
        self.page.add_style_tag(content=generic_cookie_css)

    def remove_ads(self):
        remove_ads_js = """
            // Extending the script to also target Google Ads elements
            const adSelectors = [
                'iframe[id*="google_ads"]',
                'iframe[name*="google_ads"]',
                '.adsbygoogle',
                // Add more selectors as needed
            ];
            adSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(element => {
                    element.remove();
                });
            });
        """
        self.page.evaluate(remove_ads_js)

        hide_ads_css = """
            iframe[id*='google_ads'],
            iframe[name*='google_ads'],
            .adsbygoogle {
                display: none !important;
            }
            /* Add more selectors as needed */
        """
        self.page.add_style_tag(content=hide_ads_css)
