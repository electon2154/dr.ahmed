from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    """
    Form for creating and editing products
    """
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'stock', 'discount', 'description', 'image', 'is_available']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter product name',
                'required': True
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Skincare, Moisturizer',
                'required': True
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0',
                'min': '0',
                'required': True
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input form-textarea',
                'placeholder': 'Enter detailed product description',
                'rows': 5,
                'required': True
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-checkbox-input'
            })
        }
        
        labels = {
            'name': 'Product Name',
            'category': 'Category',
            'price': 'Price (IQD)',
            'stock': 'Stock Quantity',
            'discount': 'Discount (IQD)',
            'description': 'Description',
            'image': 'Product Image',
            'is_available': 'Available for Sale'
        }
        
        help_texts = {
            'discount': 'Optional: Enter discount amount in IQD',
            'image': 'Supported formats: JPG, PNG, GIF (Max: 5MB)',
            'is_available': 'Check if this product should be available for customers to purchase'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields required
        self.fields['name'].required = True
        self.fields['category'].required = True
        self.fields['price'].required = True
        self.fields['stock'].required = True
        self.fields['description'].required = True
        
        # Set default value for is_available
        if not self.instance.pk:  # New product
            self.fields['is_available'].initial = True
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Price cannot be negative.')
        return price
    
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError('Stock quantity cannot be negative.')
        return stock
    
    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is not None and discount < 0:
            raise forms.ValidationError('Discount cannot be negative.')
        return discount
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('Product name must be at least 2 characters long.')
        return name
    
    def clean_category(self):
        category = self.cleaned_data.get('category')
        if category:
            category = category.strip().title()  # Capitalize first letter of each word
        return category
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description:
            description = description.strip()
            if len(description) < 10:
                raise forms.ValidationError('Description must be at least 10 characters long.')
        return description
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (5MB limit)
            if image.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError('Image file size cannot exceed 5MB.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if image.content_type not in allowed_types:
                raise forms.ValidationError('Only JPEG, PNG, and GIF images are allowed.')
        
        return image