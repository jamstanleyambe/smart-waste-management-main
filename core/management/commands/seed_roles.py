from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Role

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed initial roles and admin user for the waste management system'

    def handle(self, *args, **options):
        self.stdout.write('Creating roles...')
        
        # Create roles with default permissions
        roles_data = [
            {
                'name': 'ADMIN',
                'description': 'Full system administrator with all permissions',
                'permissions': {
                    'can_manage_users': True,
                    'can_manage_roles': True,
                    'can_manage_bins': True,
                    'can_manage_trucks': True,
                    'can_manage_dumping_spots': True,
                    'can_view_reports': True,
                    'can_manage_system': True
                }
            },
            {
                'name': 'MANAGER',
                'description': 'Manager with oversight permissions',
                'permissions': {
                    'can_manage_users': False,
                    'can_manage_roles': False,
                    'can_manage_bins': True,
                    'can_manage_trucks': True,
                    'can_manage_dumping_spots': True,
                    'can_view_reports': True,
                    'can_manage_system': False
                }
            },
            {
                'name': 'DRIVER',
                'description': 'Truck driver with limited permissions',
                'permissions': {
                    'can_manage_users': False,
                    'can_manage_roles': False,
                    'can_manage_bins': False,
                    'can_manage_trucks': False,
                    'can_manage_dumping_spots': False,
                    'can_view_reports': True,
                    'can_manage_system': False
                }
            },
            {
                'name': 'OPERATOR',
                'description': 'System operator with data management permissions',
                'permissions': {
                    'can_manage_users': False,
                    'can_manage_roles': False,
                    'can_manage_bins': True,
                    'can_manage_trucks': True,
                    'can_manage_dumping_spots': True,
                    'can_view_reports': True,
                    'can_manage_system': False
                }
            },
            {
                'name': 'VIEWER',
                'description': 'Read-only access to system data',
                'permissions': {
                    'can_manage_users': False,
                    'can_manage_roles': False,
                    'can_manage_bins': False,
                    'can_manage_trucks': False,
                    'can_manage_dumping_spots': False,
                    'can_view_reports': True,
                    'can_manage_system': False
                }
            }
        ]
        
        created_roles = []
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'permissions': role_data['permissions']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created role: {role.get_name_display()}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Role already exists: {role.get_name_display()}')
                )
            created_roles.append(role)
        
        # Create admin user if it doesn't exist
        admin_role = Role.objects.get(name='ADMIN')
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@wastemanagement.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': admin_role,
                'employee_id': 'ADMIN001',
                'department': 'IT',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS('Created admin user: admin (password: admin123)')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Admin user already exists')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded roles and admin user!')
        )
