#!/usr/bin/env python3
"""
Custom forms for the Smart Waste Management system
"""

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import CameraImage, Camera
from PIL import Image
import io

class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget for multiple file uploads"""
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    """Custom field for multiple file uploads"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class BulkImageUploadForm(forms.Form):
    """Form for bulk image upload"""
    
    camera = forms.ModelChoiceField(
        queryset=Camera.objects.all(),
        required=True,
        help_text="Select the camera for these images"
    )
    
    images = MultipleFileField(
        required=True,
        help_text="Select multiple images to upload (JPG, PNG, GIF supported)"
    )
    
    analysis_type = forms.ChoiceField(
        choices=[
            ('WASTE_DETECTION', 'Waste Detection'),
            ('FILL_LEVEL', 'Fill Level Analysis'),
            ('GENERAL', 'General'),
            ('MAINTENANCE', 'Maintenance Check'),
        ],
        initial='GENERAL',
        help_text="Analysis type for all uploaded images"
    )
    
    def clean_images(self):
        """Validate uploaded images"""
        images = self.files.getlist('images')
        
        if not images:
            raise forms.ValidationError("Please select at least one image to upload.")
        
        if len(images) > 20:
            raise forms.ValidationError("You can upload a maximum of 20 images at once.")
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        valid_mime_types = ['image/jpeg', 'image/png', 'image/gif']
        
        for image in images:
            # Check file extension
            if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError(f"File '{image.name}' has an invalid extension. Only JPG, PNG, and GIF files are allowed.")
            
            # Check MIME type
            if image.content_type not in valid_mime_types:
                raise forms.ValidationError(f"File '{image.name}' has an invalid MIME type. Only image files are allowed.")
            
            # Check file size (max 10MB per image)
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError(f"File '{image.name}' is too large. Maximum file size is 10MB.")
        
        return images
    
    def save(self):
        """Save all uploaded images"""
        camera = self.cleaned_data['camera']
        images = self.cleaned_data['images']
        analysis_type = self.cleaned_data['analysis_type']
        
        created_images = []
        
        for image_file in images:
            # Create CameraImage instance
            camera_image = CameraImage(
                camera=camera,
                analysis_type=analysis_type,
                image=image_file
            )
            camera_image.save()
            created_images.append(camera_image)
        
        return created_images

class SingleImageUploadForm(forms.ModelForm):
    """Enhanced single image upload form"""
    
    class Meta:
        model = CameraImage
        fields = ['camera', 'image', 'analysis_type']
        widgets = {
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control'
            }),
            'camera': forms.Select(attrs={'class': 'form-control'}),
            'analysis_type': forms.Select(attrs={'class': 'form-control'})
        }
    
    def clean_image(self):
        """Validate single image upload"""
        image = self.cleaned_data.get('image')
        
        if not image:
            return image
        
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
            raise forms.ValidationError("Invalid file extension. Only JPG, PNG, and GIF files are allowed.")
        
        # Check MIME type
        valid_mime_types = ['image/jpeg', 'image/png', 'image/gif']
        if image.content_type not in valid_mime_types:
            raise forms.ValidationError("Invalid MIME type. Only image files are allowed.")
        
        # Check file size (max 10MB)
        if image.size > 10 * 1024 * 1024:
            raise forms.ValidationError("File is too large. Maximum file size is 10MB.")
        
        return image
