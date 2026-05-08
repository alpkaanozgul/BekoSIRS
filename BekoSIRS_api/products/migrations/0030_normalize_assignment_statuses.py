from django.db import migrations


def normalize_assignment_statuses(apps, schema_editor):
    ProductAssignment = apps.get_model('products', 'ProductAssignment')
    ProductAssignment.objects.filter(status='PENDING').update(status='PLANNED')
    ProductAssignment.objects.filter(status='delivered').update(status='DELIVERED')


def reverse_normalize_assignment_statuses(apps, schema_editor):
    # Keep the normalized values on rollback; old mixed-case values were invalid.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0029_product_created_at'),
    ]

    operations = [
        migrations.RunPython(normalize_assignment_statuses, reverse_normalize_assignment_statuses),
    ]
