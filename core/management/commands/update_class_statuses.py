from django.core.management.base import BaseCommand
from core.models import SchoolClass


class Command(BaseCommand):
    help = 'Updates the status of school classes (e.g., marks as graduated).'

    def handle(self, *args, **options):
        updated_count = 0
        for school_class in SchoolClass.objects.filter(status='active'):
            if school_class.update_status_based_on_grade():
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully updated status for class {school_class.full_name()} to "graduated".'
                ))
        self.stdout.write(self.style.SUCCESS(
            f'Finished updating class statuses. Total updated: {updated_count}'
        ))