from chat.models import UserMemory

def get_user_memory(user):
    return UserMemory.objects.get_or_create(user=user)[0]