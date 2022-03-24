# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class IwonScrapyAddressPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter.get('address'):
            return item
        else:
            raise DropItem(f"Missing address in {item}")


class DuplicatesPipeline:

    def __init__(self):
        self.names_with_address_seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        name_with_address = (adapter['name'] + ' ' + adapter['address'])
        if name_with_address in self.names_with_address_seen:
            raise DropItem(f"Duplicate item found: {item!r}")
        else:
            self.names_with_address_seen.add(name_with_address)
            return item
