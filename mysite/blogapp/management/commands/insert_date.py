from django.core.management import BaseCommand
from django.db import transaction

from blogapp.models import Article, Author, Tag, Category


class Command(BaseCommand):
    """
    Create data for the blogapp
    """

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('create data for blog app'))

        authors_data = [
            {'name': 'Pushkin', 'bio': 'Bio of Pushkin'},
            {'name': 'Esenin', 'bio': 'Bio of Esenin'},
            {'name': 'Dostoevsky', 'bio': 'Bio of Dostoevsky'}
        ]
        authors = [
            Author.objects.get_or_create(name=author_data['name'], defaults={'bio': author_data['bio']})[0]
            for author_data in authors_data
        ]

        categories_data = [
            {'name': 'Poetry'},
            {'name': 'Fiction'},
            {'name': 'Non-Fiction'}
        ]
        categories = [
            Category.objects.get_or_create(name=category_data['name'])[0]
            for category_data in categories_data
        ]

        tags_data = [
            {'name': 'Classic'},
            {'name': 'Romance'},
            {'name': 'Thriller'}
        ]
        tags = [
            Tag.objects.get_or_create(name=tag_data['name'])[0]
            for tag_data in tags_data
        ]

        articles_data = [
            {
                'title': 'Poem 1',
                'content': 'Content of Poem 1',
                'author': authors[0],
                'category': categories[0],
                'tags': [tags[0], tags[1]]
            },
            {
                'title': 'Short Story',
                'content': 'Content of Short Story',
                'author': authors[1],
                'category': categories[1],
                'tags': [tags[1]]
            },
            {
                'title': 'Novel',
                'content': 'Content of Novel',
                'author': authors[2],
                'category': categories[2],
                'tags': [tags[2]]
            }
        ]

        for article_data in articles_data:
            article, created = Article.objects.get_or_create(
                title=article_data['title'],
                content=article_data['content'],
                author=article_data['author'],
                category=article_data['category']
            )
            article.tags.set(article_data['tags'])

        self.stdout.write(self.style.SUCCESS("Data created successfully"))
