from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.contrib.syndication.views import Feed
from django.urls import reverse, reverse_lazy
from .models import Article


class ArticleListView(ListView):
    model = Article
    template_name = 'blogapp/article_list.html'
    context_object_name = 'articles'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('author', 'category')
        queryset = queryset.prefetch_related('tags')
        queryset = queryset.defer('content')
        return queryset


class ArticleDetailView(DetailView):
    model = Article


class LatestArticlesFeed(Feed):
    title = 'Blog articles (latest)'
    description = 'Updates on changes and addition blog articles'
    link = reverse_lazy('blogapp:articles-list')

    def items(self):
        return (
            Article.objects.filter(pub_date__isnull=False).order_by('-pub_date')[:5]
        )

    def item_title(self, item: Article):
        return item.title

    def item_description(self, item: Article):
        return item.content[:20]

