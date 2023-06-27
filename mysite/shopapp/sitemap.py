from django.contrib.sitemaps import Sitemap

from .models import Product


class ShopSitemap(Sitemap):
    changefreq = 'never'
    priority = 1

    def items(self):
        return (
            Product.objects.filter(archived=False)
        )

    def location(self, obj):
        return obj.get_absolute_url()


