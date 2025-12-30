from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ChatSession, Message
from documents.openai_client import OpenAIClient
from documents.pinecone_client import PineconeClient
import json


@login_required
def chat_home(request):
    """Chat home page - list all sessions"""
    sessions = ChatSession.objects.filter(user=request.user)
    return render(request, 'chat/home.html', {'sessions': sessions})


@login_required
def chat_session(request, session_id=None):
    """Chat interface for a specific session"""
    
    if session_id:
        # Load existing session
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    else:
        # Create new session
        session = ChatSession.objects.create(
            user=request.user,
            title="New Chat"
        )
        return redirect('chat_session', session_id=session.id)
    
    # Get all messages in session
    messages = session.messages.all()
    
    # Get all sessions for sidebar
    all_sessions = ChatSession.objects.filter(user=request.user)
    
    context = {
        'session': session,
        'messages': messages,
        'all_sessions': all_sessions,
    }
    
    return render(request, 'chat/session.html', context)


@login_required
@require_POST
def send_message(request, session_id):
    """Handle sending a message and getting AI response"""
    
    try:
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        
        # Get user message from request
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Save user message
        user_msg = Message.objects.create(
            session=session,
            role=Message.Role.USER,
            content=user_message
        )
        
        # Update session title if it's the first message
        if session.messages.count() == 1:
            # Use first few words as title
            title_words = user_message.split()[:5]
            session.title = ' '.join(title_words) + ('...' if len(title_words) == 5 else '')
            session.save()
        
        # Initialize clients
        openai_client = OpenAIClient()
        pinecone_client = PineconeClient()
        
        # Create embedding for user query
        query_embedding = openai_client.create_embedding(user_message)
        
        # Search Pinecone for relevant chunks (filter by user_id)
        search_results = pinecone_client.query_vectors(
            query_vector=query_embedding,
            top_k=5,
            filter_dict={"user_id": {"$eq": request.user.id}}
        )
        
        # Extract context chunks and sources
        context_chunks = []
        sources = []
        
        for result in search_results:
            metadata = result['metadata']
            context_chunks.append(metadata['text'])
            
            # Build source citation
            source = {
                'document_title': metadata.get('document_title', 'Unknown'),
                'chunk_index': metadata.get('chunk_index', 0),
                'score': result['score']
            }
            sources.append(source)
        
        # Get conversation history (last 5 messages)
        history_messages = session.messages.order_by('-created_at')[:6][::-1]
        conversation_history = []
        
        for msg in history_messages[:-1]:  # Exclude the current user message
            conversation_history.append({
                'role': 'user' if msg.role == Message.Role.USER else 'assistant',
                'content': msg.content
            })
        
        # Generate AI response
        if context_chunks:
            ai_response = openai_client.generate_rag_response(
                query=user_message,
                context_chunks=context_chunks,
                conversation_history=conversation_history
            )
        else:
            # No relevant documents found
            ai_response = "I couldn't find any relevant information in your uploaded documents to answer this question. Please make sure you have uploaded documents related to your query."
            sources = []
        
        # Save AI message
        ai_msg = Message.objects.create(
            session=session,
            role=Message.Role.ASSISTANT,
            content=ai_response,
            sources=sources
        )
        
        # Return response
        return JsonResponse({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'content': user_msg.content,
                'created_at': user_msg.created_at.isoformat()
            },
            'ai_message': {
                'id': ai_msg.id,
                'content': ai_msg.content,
                'sources': ai_msg.sources,
                'created_at': ai_msg.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def delete_session(request, session_id):
    """Delete a chat session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def rename_session(request, session_id):
    """Rename a chat session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    data = json.loads(request.body)
    new_title = data.get('title', '').strip()
    
    if new_title:
        session.title = new_title
        session.save()
        return JsonResponse({'success': True, 'title': session.title})
    
    return JsonResponse({'error': 'Title cannot be empty'}, status=400)
