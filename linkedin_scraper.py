import parameters
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from parsel import Selector


driver = webdriver.Chrome()


def connect_to_linkedin():
    driver.get('https://www.linkedin.com')
    username = driver.find_element_by_id('session_key')
    username.send_keys(parameters.linkedin_username)
    password = driver.find_element_by_id('session_password')
    password.send_keys(parameters.linkedin_password)

    sign_in_button = driver.find_element_by_xpath('//*[@type="submit"]')
    sign_in_button.click()
    sleep(0.5)


def lookup_google():
    driver.get('https:www.google.com')
    sleep(3)
    search_query = driver.find_element_by_name('q')
    search_query.send_keys(parameters.search_query)
    search_query.send_keys(Keys.RETURN)
    sleep(3)


def parse_google_results():
    lnks = driver.find_elements_by_partial_link_text('linkedin.com')
    linkedin_urls = [lk.get_attribute('href') for lk in lnks]
    sleep(0.5)
    return linkedin_urls


def extract_profiles_data(linkedin_urls):
    # For loop to iterate over each URL in the list
    for linkedin_url in linkedin_urls:
        # get the profile URL
        driver.get(linkedin_url)
        sleep(0.2)
        sel = Selector(text=driver.page_source)
        name = sel.xpath(
            '//h1[@class="text-heading-xlarge inline t-24 v-align-middle break-words"]/text()').extract_first()

        if name:
            name = name.strip()
        job_title = sel.xpath(
            '//div[@class="text-body-medium break-words"]/text()').extract_first()
        if job_title:
            job_title = job_title.strip()
        location = sel.xpath(
            '//span[@class="text-body-small inline t-black--light break-words"]/text()').extract_first()

        if location:
            location = location.strip()
        # get email if it exists
        driver.get(linkedin_url + 'detail/contact-info')
        sel = Selector(text=driver.page_source)
        email = sel.xpath(
            '//section[@class="pv-contact-info__contact-type ci-email"]//a[@class="pv-contact-info__contact-link link-without-visited-state t-14"]/@href').extract_first()

        print(name, ":", location, ":", job_title, ":", email)
        linkedin_url = driver.current_url


def save_to_csv():
    return


def visit_google_results_pages(page=10):
    connect_to_linkedin()
    lookup_google()

    while page > 0:
        urls = parse_google_results()
        extract_profiles_data(urls)
        lookup_google()
        for pg in page:
            driver.find_element_by_id("pnnext").click()
            sleep(0.1)
        page -= 1


visit_google_results_pages()
driver.quit()
