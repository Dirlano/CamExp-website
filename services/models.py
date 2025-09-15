from django.db import models
from accounts.models import Profile
from django.utils import timezone

class ServiceListing(models.Model):
    CATEGORY_CHOICES = [
        ('it', 'Information Technology'),
        ('design', 'Design & Creative'),
        ('marketing', 'Marketing'),
        ('writing', 'Writing & Translation'),
        ('business', 'Business'),
        ('lifestyle', 'Lifestyle'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    expert = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False, help_text='Mark this service as featured')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Service Listing'
        verbose_name_plural = 'Service Listings'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class RequestPost(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    client = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='service_requests')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.CharField(
        max_length=50, 
        choices=ServiceListing.CATEGORY_CHOICES,
        blank=True,
        null=True
    )
    location = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_expert = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_requests'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Service Request'
        verbose_name_plural = 'Service Requests'
    
    def __str__(self):
        return f"{self.title} by {self.client.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(f"{self.title}-{self.client.user.username}")
        super().save(*args, **kwargs)


class Reaction(models.Model):
    REACTION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('proposal', 'Proposal'),
        ('question', 'Question'),
    ]
    
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reactions')
    post = models.ForeignKey(ServiceListing, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    request = models.ForeignKey(RequestPost, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    type = models.CharField(max_length=20, choices=REACTION_TYPES)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(post__isnull=False) | 
                    models.Q(request__isnull=False)
                ),
                name='at_least_one_related_object',
                violation_error_message='Reaction must be associated with either a post or a request.'
            )
        ]
    
    def __str__(self):
        return f"{self.user.user.username}'s {self.get_type_display()} on {self.post or self.request}"


class Rating(models.Model):
    SCORE_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    reviewer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='given_ratings')
    expert = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='ratings_received')
    score = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)
    title = models.CharField(max_length=200, blank=True, null=True)
    review = models.TextField()
    service = models.ForeignKey(ServiceListing, on_delete=models.SET_NULL, null=True, blank=True, related_name='ratings')
    request = models.ForeignKey(RequestPost, on_delete=models.SET_NULL, null=True, blank=True, related_name='ratings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['reviewer', 'expert', 'service'], ['reviewer', 'expert', 'request']]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(service__isnull=False) | 
                    models.Q(request__isnull=False)
                ),
                name='rating_has_service_or_request',
                violation_error_message='Rating must be associated with either a service or a request.'
            ),
            models.CheckConstraint(
                check=~models.Q(reviewer=models.F('expert')),
                name='cannot_rate_yourself',
                violation_error_message='You cannot rate yourself.'
            )
        ]
    
    def __str__(self):
        return f"{self.get_score_display()} - {self.reviewer.user.username} for {self.expert.user.username}"