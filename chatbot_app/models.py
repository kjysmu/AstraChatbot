from django.db import models

# Create your models here.

class Chatbot(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='chatbot_images')

    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chatbot.name} - {self.role}: {self.content[:50]}"
