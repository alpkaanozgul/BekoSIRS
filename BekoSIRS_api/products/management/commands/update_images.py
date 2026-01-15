import os
from django.core.management.base import BaseCommand
from django.db.models import Q
from products.models import Product

class Command(BaseCommand):
    help = 'Smart update of product images using normalization and substring matching'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the mapping text file')

    def normalize(self, text):
        """Removes spaces, punctuation and converts to lower case for comparison."""
        if not text: return ""
        return text.lower().replace(' ', '').replace('-', '').replace('_', '').strip()

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write('Loading all products from DB for smart matching...')
        
        # Load all products into memory to perform complex Python comparisons
        all_products = list(Product.objects.all())
        
        updated_count = 0
        not_found_count = 0

        # Create a mapping dictionary for specific hard cases (Barcode -> Name) if needed
        # manually_mapped = {'8690842487576': 'Product Name In DB'} 

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip() or '-------' in line: continue
                if 'PRODUCT ID' in line and 'IMAGE URL' in line: continue

                # Parse line
                parts = line.split(' : ')
                if len(parts) < 2: continue
                
                file_name_raw = parts[0].strip()
                image_url = parts[1].strip()

                if not image_url.startswith('http'): continue

                # ---------------------------------------------------------
                # MATCHING LOGIC
                # ---------------------------------------------------------
                matched_product = None
                match_method = ""
                
                file_norm = self.normalize(file_name_raw) # e.g. "cmx10120"

                for product in all_products:
                    # Get DB fields
                    db_name = product.name or ""
                    db_code = getattr(product, 'model_code', "") or ""
                    
                    db_name_norm = self.normalize(db_name)
                    db_code_norm = self.normalize(db_code)

                    # 1. Exact/Normalized Match (Handles spacing issues)
                    # "CMX 10120" vs "CMX10120"
                    if file_norm == db_name_norm:
                        matched_product = product
                        match_method = "Normalized Name"
                        break
                    
                    if db_code and file_norm == db_code_norm:
                        matched_product = product
                        match_method = "Normalized Code"
                        break

                    # 2. Substring Match (One name is inside the other)
                    # DB: "CEP 6464 X" | File: "CAFFEEXPERTO CE5300 CEP 6464 X KAHVE"
                    if len(db_name_norm) > 4 and db_name_norm in file_norm:
                        matched_product = product
                        match_method = "DB Name inside File Name"
                        break
                    
                    if len(file_norm) > 4 and file_norm in db_name_norm:
                        matched_product = product
                        match_method = "File Name inside DB Name"
                        break

                    # 3. Slash Split Match
                    # DB: "DO 8160 CI / CHG 81442 BX" | File: "DO 8160 CI"
                    if '/' in db_name:
                        split_names = [self.normalize(n) for n in db_name.split('/')]
                        if file_norm in split_names:
                            matched_product = product
                            match_method = "Slash Split Match"
                            break

                # ---------------------------------------------------------
                # UPDATE ACTION
                # ---------------------------------------------------------
                if matched_product:
                    try:
                        matched_product.image = image_url
                        matched_product.save()
                        # Only print if it was previously tricky to find
                        if match_method != "Normalized Name":
                            self.stdout.write(self.style.SUCCESS(f'Γ£à Matched "{file_name_raw}" to "{matched_product.name}" ({match_method})'))
                        updated_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error saving {file_name_raw}: {e}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Γ¥î Still Not Found: {file_name_raw}'))
                    not_found_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nSmart Update Complete! Updated: {updated_count}, Not Found: {not_found_count}'))

      
