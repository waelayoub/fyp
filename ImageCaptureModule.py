import time
import os
from PIL import Image
from playwright.sync_api import sync_playwright
import uuid


def wait_for_images_to_load(page, timeout=30000):
    js_check_images = """
    () => {
        return Array.from(document.images).every((img) => img.complete);
    }
    """
    page.wait_for_function(js_check_images, timeout=timeout)


def get_dimensions(page):
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

    body_height = page.evaluate(b_scroll_h)
    window_height = page.evaluate(inner_h)
    return body_height, window_height


def scroll_to_top(page):
    js_scroll_back_to_the_top = """
    () => {
        window.scrollTo(0, 0);
    }
    """
    page.evaluate(js_scroll_back_to_the_top)


def scroll_and_wait_for_images(page, timeout=30000):

    body_height, window_height = get_dimensions(page)
    scroller_number = round(body_height/window_height)

    js_scroll = """
    () => {
        window.scrollBy(0, window.innerHeight);
    }
    """

    try:
        wait_for_images_to_load(page, timeout)
    except Exception as e:
        if not (str(e).__contains__("EvalError")):
            print(e)
            print("Crawling will start even if some images has not been loaded")
            timeout = 3000
        else:
            time.sleep(1)

    for i in range(scroller_number):
        page.evaluate(js_scroll)
        time.sleep(2)
        try:
            wait_for_images_to_load(page, timeout)
        except Exception as e:
            if not (str(e).__contains__("EvalError")):
                print("Continuing crawling even with not all loaded images")
            else:
                time.sleep(1)
        print("Completion: "+str(round((i+1)/scroller_number*100, 2))+" %")
    scroll_to_top(page)


def crawl_and_capture(url, base_output_path, page, site_timeout=90000):
    try:
        page.goto(url, wait_until='networkidle', timeout=site_timeout)
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")
    finally:
        remove_disclaimer_cookies(page)
        remove_ads(page)

        scroll_and_wait_for_images(page, site_timeout)
        folder_path = base_output_path+"/"+str(uuid.uuid4())

        os.mkdir(path=folder_path)

        filename = "full_page.png"
        output_path = f"{folder_path}/{filename}"

        time.sleep(3)
        page.screenshot(path=output_path, full_page=True, animations="allow")
        print(f"Screenshot saved for {url} at {output_path}")
        split_image(output_path, folder_path, split_height=1024, image_format='png')
        page.close()


def split_image(input_path, output_directory, split_height=1024, image_format='png'):
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
        splits = img_height // split_height
        if img_height % split_height != 0:
            splits += 1

        # Split the image and save each part
        for i in range(splits):
            top = i * split_height
            bottom = min((i + 1) * split_height, img_height)

            # Crop the image
            img_cropped = img.crop((0, top, img_width, bottom))
            split_filename = os.path.join(output_directory, f"split_{i}.{image_format}")

            # Save the cropped image
            img_cropped.save(split_filename)
            print(f"Saved split image: {split_filename}")


def remove_disclaimer_cookies(page):

    # generic_cookie_js = """
    #     const selectors = [
    #         'cookie', 'consent', 'gdpr', 'disclaimer', 'privacy', 'popup', 'overlay',
    #         'notice', 'banner', 'policy', 'compliance'
    #     ].map(selector => selector.toLowerCase()); // Convert all selectors to lowercase
    #
    #     document.querySelectorAll('[id], [class]').forEach(element => {
    #         // Convert element id and class to lowercase and check if any selector matches
    #         const id = element.id.toString();
    #         const classes = element.className.toString();
    #         if (selectors.some(selector => id.includes(selector) || classes.includes(selector))) {
    #             element.remove();
    #         }
    #     });
    # """

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
    page.evaluate(generic_cookie_js)
    page.add_style_tag(content=generic_cookie_css)


def remove_ads(page):
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
    page.evaluate(remove_ads_js)

    hide_ads_css = """
        iframe[id*='google_ads'],
        iframe[name*='google_ads'],
        .adsbygoogle {
            display: none !important;
        }
        /* Add more selectors as needed */
    """
    page.add_style_tag(content=hide_ads_css)


def main():
    # start_url = "https://www.youtube.com"
    # start_url ="https://www.mtv.com.lb"
    # start_url = "https://www.lbcgroup.tv"
    # start_url = "https://www.aljadeed.tv"
    # start_url = "https://www.tradingview.com/markets/cryptocurrencies/#cryptocurrencies-market-summary"
    start_url = input("Insert url: ")

    output_directory = "./images"

    with sync_playwright() as p:

        browser_type = p.chromium
        context = browser_type.launch_persistent_context("", headless=False, args=[
            "--headless=new",
            f'--load-extension=./fihnjjcciajhdojfnbdddfaoknhalnja/3.5.0_0',
            f'--disable-extensions-except=./fihnjjcciajhdojfnbdddfaoknhalnja/3.5.0_0'
        ])

        if len(context.background_pages) == 0:
            background_page = context.wait_for_event('backgroundpage')
        else:
            background_page = context.background_pages[0]
        page = context.new_page()

        crawl_and_capture(start_url, output_directory, page)

        context.close()


if __name__ == "__main__":
    main()
