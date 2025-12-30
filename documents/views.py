from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Document
from .forms import DocumentForm
from .tasks import process_document, delete_document_vectors
import threading

@login_required
def document_list(request):
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'documents/list.html', {'documents': documents})

@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save()
            
            # Trigger processing in background thread
            thread = threading.Thread(target=process_document, args=(doc.id,))
            thread.start()
            
            messages.success(request, f'Document "{doc.title}" uploaded successfully! Processing started.')
            return redirect('document_list')
    else:
        form = DocumentForm()
    return render(request, 'documents/upload.html', {'form': form})

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    
    if request.method == 'POST':
        title = document.title
        
        # Delete vectors from Pinecone
        try:
            delete_document_vectors(document.id)
        except Exception as e:
            messages.warning(request, f'Could not delete vectors: {str(e)}')
        
        # Delete document
        document.delete()
        messages.success(request, f'Document "{title}" deleted successfully.')
        return redirect('document_list')
    
    return render(request, 'documents/delete_confirm.html', {'document': document})

