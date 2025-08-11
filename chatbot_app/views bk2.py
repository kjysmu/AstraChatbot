from django.shortcuts import render
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from django.http import JsonResponse
from django.utils.text import Truncator
import json
from .models import Chatbot, ChatMessage

llama_client = OllamaLLM(model="llama3.1")

def fetch_chat_history(request):
    chatbot_name = request.GET.get('chatbot')

    try:
        chatbot = Chatbot.objects.get(name=chatbot_name)
        chat_history = ChatMessage.objects.filter(chatbot=chatbot).values('role', 'content')
        chatbot_image = chatbot.image.url

        return JsonResponse({
            'chat_history': list(chat_history),
            'chatbot_image': chatbot_image,
        })
    except Chatbot.DoesNotExist:
        return JsonResponse({'error': 'Chatbot not found'}, status=404)


def update_bot_list(request, chatbots_with_images, active_bot_name, recent_message):
    """Update the recent message and move the active bot to the top of the list."""
    for bot in chatbots_with_images:
        if bot['name'] == active_bot_name:
            bot['recent_message'] = recent_message  # Update the recent message
            chatbots_with_images.remove(bot)  # Remove the bot from the list
            chatbots_with_images.insert(0, bot)  # Insert it at the top
            break
    # Save the updated order to the session
    request.session['reordered_bots'] = chatbots_with_images
    return chatbots_with_images

def chatbot_interface(request):
    selected_chatbot_name = request.GET.get('chatbot', None)
    chat_history = request.session.get('chat_histories', {})

    # Fetch all chatbots from the database
    chatbots = Chatbot.objects.all()
    
    chatbots_with_images = []
    for bot in chatbots:
        recent_message_obj = ChatMessage.objects.filter(chatbot=bot).order_by('-timestamp').first()
        recent_message = recent_message_obj.content if recent_message_obj else ""
        truncated_message = Truncator(recent_message).chars(35)

        chatbots_with_images.append({
            "name": bot.name,
            "image": bot.image.url if bot.image else "images/placeholder.png",
            "recent_message": truncated_message
        })

    chatbots_with_images = request.session.get('reordered_bots', chatbots_with_images)

    selected_chatbot_image = None
    if selected_chatbot_name:
        selected_chatbot = Chatbot.objects.filter(name=selected_chatbot_name).first()
        if selected_chatbot:
            selected_chatbot_image = selected_chatbot.image.url

    if request.method == 'POST' and selected_chatbot_name:
        try:
            data = json.loads(request.body)
            user_message = data.get('user_message', '')

            if user_message:
                chatbot = Chatbot.objects.get(name=selected_chatbot_name)

                # Save user message
                ChatMessage.objects.create(chatbot=chatbot, role="user", content=user_message)

                # Generate bot response
                prompt_template = ChatPromptTemplate.from_template(chatbot.personality)
                context = "\n".join([
                    f"{m.role.capitalize()}: {m.content}"
                    for m in ChatMessage.objects.filter(chatbot=chatbot).order_by('timestamp')
                ])
                prompt = f"{chatbot.personality}\n{context}\nUser: {user_message}\nAI:"
                bot_response = llama_client.invoke(prompt)

                # Save bot response
                ChatMessage.objects.create(chatbot=chatbot, role="assistant", content=bot_response)

                recent_message = Truncator(bot_response).chars(35)
                updated_bots = update_bot_list(request, chatbots_with_images, selected_chatbot_name, recent_message)

                return JsonResponse({
                    "response": bot_response,
                    "recent_message": recent_message,
                    "updated_bots": updated_bots
                })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return render(request, 'chatbot_app/chatbot_interface.html', {
        'chatbots_with_images': chatbots_with_images,
        'selected_chatbot': selected_chatbot_name,
        'selected_chatbot_image': selected_chatbot_image,
        'chat_history': ChatMessage.objects.filter(chatbot__name=selected_chatbot_name).values('role', 'content')
            if selected_chatbot_name else [],
    })
