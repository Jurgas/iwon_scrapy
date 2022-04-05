import io
import scrapy
import re
import fitz

from iwon_scrapy.items import IwonScrapyItem


class FacilitiesSpider(scrapy.Spider):
    name = 'facilities'

    custom_settings = {
        'DEPTH_LIMIT': 1,
    }

    facilities_names = [
        'Powiatowe Centrum Pomocy Rodzinie',
        'Ośrodek Pomocy Społecznej',
        'Miejski Ośrodek Pomocy Społecznej',
        'Gminny Ośrodek Pomocy Społecznej',
        'Ośrodek Wspomagania Rodziny',
        'Dom Dziecka',
        'Dom Rodzinny',
        'Ośrodek Interwencji Kryzysowej',
        'Dom Pomocy Społecznej',
        'Środowiskowy Dom Samopomocy',
        'Punkt Informacyjno-Koordynacyjny dla Osób z Niepełnosprawnościami',
        'Punkt Informacyjno-Koordynacyjny',
        'Punkt Informacyjno-Koordynacyjny dla Osób z Niepełnosprawnością Intelektualną',
        'Stołeczne Centrum Osób Niepełnosprawnych',
        'Miejski Zespół Orzekania o Niepełnosprawności',
        'Państwowy Fundusz Rehabilitacji Osób Niepełnosprawnych',
        'Centrum Aktywności Międzypokoleniowej',
        'Dom pomocy',
        'Zespół Domów Pomocy Społecznej'
    ]

    address_regex = r"((\bul\.|\bulica\b|\bos\.|\bosiedle\b|\baleja\b|\bAleja\b)((?!\bul\.|\bulica\b|\bos\.|\bosiedle\b|\baleja\b|\bAleja\b)[a-zA-ZżźćńółęąśŻŹĆĄŚĘŁÓŃ\s\.]){0,100}\d+[a-zA-Z]*(\s*(/|m.)\s*\d+[a-zA-Z]*)?)"
    post_code_regex = r"\s\d{2}-\d{3}\s"
    phone_regex = r"(((\+|0{2})\d{2}[-\s]?)?((\(\s?0?\d{2}\s?\))|\d{2})[\s-]?(\d[\s-]?){6}\d)"
    website_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

    start_urls = [
        # 'https://opsochota.waw.pl/strona-3369-instytucje_skierowane_do_osob_z.html'
        'https://bip.pcpr.powiat.poznan.pl/index.php/przydatne-adresy/wykaz-jednostek-organizacyjnych-pomocy-spolecznej-i-pieczy-zastepczej-w-powiecie-poznanskim/'
        # 'file:///Users/sebastian/PycharmProjects/pythonProject/rejestr.pdf'
        # 'https://www.poznan.uw.gov.pl/system/files/zalaczniki/rejestr_domow_pomocy_spolecznej_-_aktualizacja_22.03.2022_r.pdf'
    ]

    def parse(self, response, **kwargs):
        page_text = ""
        file = getattr(self, 'file', False)
        if file:
            with fitz.open("pdf", io.BytesIO(response.body)) as doc:
                for doc_page in doc:
                    page_text += doc_page.get_text()
        else:
            page_text = response.xpath('//body//text()').getall()
            page_text = ' '.join(_ for _ in page_text)

        regex_names = '(' + '|'.join(_ for _ in self.facilities_names) + ')'

        page_text = ' '.join(page_text.split())

        split_text = re.split(regex_names, page_text)
        split_text = [x for x in split_text if x]

        current_facility = None
        for item in split_text:
            item = item.strip()
            if item in self.facilities_names:
                current_facility = item
            elif current_facility is not None:
                facility = IwonScrapyItem(name=current_facility)

                address = ''
                address_re = re.findall(self.address_regex, item)
                if len(address_re):
                    address = address_re[0][0]
                post_code_re = re.findall(self.post_code_regex, item)
                if len(post_code_re) and len(address):
                    address = address + ', ' + post_code_re[0].strip()
                elif len(post_code_re):
                    address = post_code_re[0].strip()

                if len(address):
                    facility['address'] = address.strip()

                phone_re = re.findall(self.phone_regex, item)
                if phone_re:
                    facility['phone'] = phone_re[0][0]

                website_re = re.findall(self.website_regex, item)
                if len(website_re):
                    facility['website'] = website_re[0][0]

                email_re = re.findall(self.email_regex, item)
                if len(email_re):
                    facility['email'] = email_re[0]

                yield facility

        follow_links = getattr(self, 'follow_links', False)
        if follow_links:
            for href in response.css('a::attr(href)'):
                if '://' in href.get():
                    yield response.follow(href, callback=self.parse)
