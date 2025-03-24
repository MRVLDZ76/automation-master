from django.core.management.base import BaseCommand
from django.db import transaction
from automation.models import ScrapingTask, Business, Category, Level
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update all businesses in a scraping task with new destination, country, level, and category information'

    def add_arguments(self, parser):
        parser.add_argument('task_id', type=int, help='ID of the scraping task to update')
        parser.add_argument('--country', required=True, help='Country name to set for all businesses')
        parser.add_argument('--destination', required=True, help='Destination name (city) to set for all businesses')
        parser.add_argument('--level-id', type=int, required=True, help='Level ID to set for the task and businesses')
        parser.add_argument('--level-name', help='Level name (for display purposes only)')
        parser.add_argument('--category-id', type=int, required=True, help='Category ID to set as main category')
        parser.add_argument('--category-name', help='Category name (for display purposes only)')
        parser.add_argument('--country-id', type=int, help='Optional country ID from the database')
        parser.add_argument('--destination-id', type=int, help='Optional destination ID from the database')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')

    @transaction.atomic
    def handle(self, *args, **options):
        task_id = options['task_id']
        country = options['country']
        destination = options['destination']
        level_id = options['level_id']
        level_name = options.get('level_name', '')
        category_id = options['category_id']
        category_name = options.get('category_name', '')
        country_id = options.get('country_id')
        destination_id = options.get('destination_id')
        dry_run = options.get('dry_run', False)

        try:
            # Get the scraping task
            task = ScrapingTask.objects.get(id=task_id)
            
            # Get the Category instance
            try:
                category = Category.objects.get(id=category_id)
                if not category_name:
                    category_name = category.title  # Using .title instead of .name based on your admin.py
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Category with ID {category_id} does not exist"))
                return
            
            # Get the Level instance
            try:
                level = Level.objects.get(id=level_id)
                if not level_name:
                    level_name = level.title  # Using .title instead of .name based on your admin.py
            except Level.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Level with ID {level_id} does not exist"))
                return
            
            # Get all businesses for this task
            businesses = Business.objects.filter(task=task)
            business_count = businesses.count()
            
            if business_count == 0:
                self.stdout.write(self.style.WARNING(f"No businesses found for task ID {task_id}"))
                return
            
            self.stdout.write(self.style.SUCCESS(f"Found {business_count} businesses for task ID {task_id}"))
            
            if dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f"DRY RUN: Would update {business_count} businesses with:"
                    f"\n- Country: {country}"
                    f"\n- Destination: {destination}"
                    f"\n- Level: {level_name} (ID: {level_id})"
                    f"\n- Main Category: {category_name} (ID: {category_id})"
                ))
                return
            
            # Update task fields if needed
            if task.main_category_id != category_id or task.level_id != level_id:
                task.main_category = category  # This is correct if task.main_category is a ForeignKey
                task.level = level  # This is correct if task.level is a ForeignKey
                #task.scraped_at = timezone.now()
                task.save(update_fields=['main_category', 'level'])
                self.stdout.write(self.style.SUCCESS(f"Updated task with new main_category and level"))
            
            # Update all businesses
            for business in businesses:
                business.country = country
                business.city = destination
                business.form_country_name = country
                business.form_destination_name = destination
                
                # Store the level name/title instead of the Level instance
                business.level = level.title  # Use a string value (title) instead of the Level instance
                
                # For main_category, check if it's a CharField or a ManyToManyField
                if hasattr(business, 'main_category') and hasattr(business.main_category, 'add'):
                    # This is a ManyToManyField
                    business.main_category.add(category)
                else:
                    # This is likely a CharField
                    business.main_category = category.title
                
                # Set IDs if provided
                if country_id:
                    business.form_country_id = country_id
                    business.country_id = country_id
                
                if destination_id:
                    business.form_destination_id = destination_id
                    business.destination_id = destination_id
                
                business.save()
                
                # Log each business update for debugging
                logger.info(f"Updating Business {business.id}: {business.project_title}")
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully updated {business_count} businesses for task ID {task_id} with:"
                f"\n- Country: {country}"
                f"\n- Destination: {destination}"
                f"\n- Level: {level_name} (ID: {level_id})"
                f"\n- Main Category: {category_name} (ID: {category_id})"
            ))
            
        except ScrapingTask.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Scraping task with ID {task_id} does not exist"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating businesses: {str(e)}"))
            logger.error(f"Error in update_business_data command: {str(e)}", exc_info=True)




# python manage.py update_business_data 51 --country="United States" --destination="Boston" --level-id=2 --category-id=43 --category-name="Marketing Services" --level-name="Business Support"

# python manage.py update_business_data 51 --country="United States" --destination="Boston" --level-id=2 --category-id=43 --category-name="Marketing Services" --level-name="Business Support" --dry-run
