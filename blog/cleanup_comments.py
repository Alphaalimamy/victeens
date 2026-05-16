from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import Comment
from datetime import timedelta


class Command(BaseCommand):
    help = 'Clean up old spam and rejected comments'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete comments older than X days (default: 30)'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete spam and rejected comments older than cutoff date
        deleted_count = Comment.objects.filter(
            status__in=[Comment.Status.SPAM, Comment.Status.REJECTED],
            created_at__lt=cutoff_date
        ).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} old comments.')
        )