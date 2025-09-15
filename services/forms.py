from django import forms
from .models import ServiceListing, RequestPost, Reaction, Rating
from django.utils.text import slugify

class ServiceForm(forms.ModelForm):
    class Meta:
        model = ServiceListing
        fields = ("title", "description", "price", "category", "location")
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200',
                'placeholder': 'e.g., Professional Web Development',
                'x-model': 'title',
                '@input': 'updateSlug()'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200 resize-none',
                'rows': 6,
                'placeholder': 'Describe your service in detail, including what makes it unique...',
                'x-model': 'description'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200',
                'placeholder': 'Enter price in FCFA',
                'min': '100',
                'step': '100',
                'x-model': 'price'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200',
                'x-model': 'category'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200',
                'placeholder': 'e.g., Douala, Bonaberi',
                'x-model': 'location',
                '@focus': 'getUserLocation()'
            }),
        }
        help_texts = {
            'price': 'Minimum price is 100 FCFA',
            'category': 'Choose the most relevant category for your service',
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 10:
            raise forms.ValidationError('Title must be at least 10 characters long')
        return title

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 100:
            raise forms.ValidationError('Price must be at least 100 FCFA')
        return price

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 50:
            raise forms.ValidationError('Description should be at least 50 characters long')
        return description

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.title)
        if commit:
            instance.save()
        return instance


class RequestForm(forms.ModelForm):
    class Meta:
        model = RequestPost
        fields = ("title", "description", "budget", "category", "location")
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200',
                'placeholder': 'What service are you looking for?',
                'x-model': 'title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200 resize-none',
                'rows': 6,
                'placeholder': 'Describe your project in detail, including your requirements and expectations...',
                'x-model': 'description'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200',
                'placeholder': 'Your budget in FCFA (optional)',
                'min': '0',
                'step': '1000',
                'x-model': 'budget'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200',
                'x-model': 'category'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200',
                'placeholder': 'Where do you need this service?',
                'x-model': 'location'
            }),
        }
        help_texts = {
            'budget': 'Leave blank to discuss budget with experts',
            'category': 'Select the most relevant category for your request',
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 10:
            raise forms.ValidationError('Title must be at least 10 characters long')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 30:
            raise forms.ValidationError('Please provide a more detailed description (at least 30 characters)')
        return description

    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget is not None and budget < 0:
            raise forms.ValidationError('Budget cannot be negative')
        return budget


class ReactionForm(forms.ModelForm):
    class Meta:
        model = Reaction
        fields = ("type", "content")
        widgets = {
            'type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200 resize-none',
                'rows': 3,
                'placeholder': 'Add your comment here...'
            }),
        }
        help_texts = {
            'type': 'Select the type of reaction',
            'content': 'Enter your comment or message',
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ("score", "title", "review", "service", "request", "expert")
        widgets = {
            'score': forms.Select(choices=Rating.SCORE_CHOICES, attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-warning focus:border-transparent transition-all duration-200',
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-warning focus:border-transparent transition-all duration-200',
                'placeholder': 'Summarize your experience in a few words',
                'maxlength': '200'
            }),
            'review': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-warning focus:border-transparent transition-all duration-200 resize-none',
                'rows': 6,
                'placeholder': 'Share your detailed experience with this expert...',
                'maxlength': '1000'
            }),
            'service': forms.HiddenInput(),
            'request': forms.HiddenInput(),
            'expert': forms.HiddenInput(),
        }
        help_texts = {
            'score': 'Rate your overall satisfaction (1-5)',
            'title': 'A brief summary of your review',
            'review': 'Share details about your experience',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make these fields optional in the form
        self.fields['title'].required = False
        self.fields['service'].required = False
        self.fields['request'].required = False

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        request = cleaned_data.get('request')
        
        # Ensure either service or request is provided, but not both
        if not service and not request:
            raise forms.ValidationError('You must select either a service or a request to rate.')
        if service and request:
            raise forms.ValidationError('You can only rate either a service or a request, not both.')
            
        return cleaned_data


class ProposalForm(forms.Form):
    """Form for expert proposals to service requests"""
    proposal_title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent transition-all duration-200',
            'placeholder': 'e.g., Professional Web Development Solution with Modern Design'
        })
    )
    executive_summary = forms.CharField(
        max_length=300,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent transition-all duration-200 resize-none',
            'rows': 4,
            'placeholder': 'Provide a compelling overview of your approach and why you\'re the best choice for this project...'
        })
    )
    detailed_proposal = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent transition-all duration-200 resize-none',
            'rows': 8,
            'placeholder': 'Detail your approach, methodology, deliverables, and how you\'ll solve the client\'s problem...'
        })
    )
    proposed_amount = forms.DecimalField(
        min_value=100,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter amount in FCFA'
        })
    )
    estimated_timeline = forms.ChoiceField(
        choices=[
            ('', 'Select timeline'),
            ('1-3_days', '1-3 days'),
            ('1_week', '1 week'),
            ('2_weeks', '2 weeks'),
            ('1_month', '1 month'),
            ('2_months', '2 months'),
            ('3_months', '3 months'),
            ('custom', 'Custom'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent transition-all duration-200'
        })
    )
    custom_timeline_text = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent transition-all duration-200',
            'placeholder': 'e.g., 6 weeks with 2-week sprints'
        })
    )
    deliverables = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent transition-all duration-200 resize-none',
            'rows': 4,
            'placeholder': 'List all deliverables the client will receive (e.g., source code, documentation, design files, etc.)'
        })
    )
    additional_services = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent transition-all duration-200 resize-none',
            'rows': 3,
            'placeholder': 'Any additional services you can offer (maintenance, support, training, etc.)'
        })
    )
    why_choose_me = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-info focus:border-transparent transition-all duration-200 resize-none',
            'rows': 4,
            'placeholder': 'Highlight your unique qualifications, relevant experience, and what makes you the best choice for this project...'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        timeline = cleaned_data.get('estimated_timeline')
        custom_timeline = cleaned_data.get('custom_timeline_text')
        
        if timeline == 'custom' and not custom_timeline:
            raise forms.ValidationError('Please provide custom timeline details when selecting custom timeline')
        
        return cleaned_data
