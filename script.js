// DOM Elements
const chatHistory = document.querySelector('.chat-history');
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const submitBtn = document.getElementById('submit-btn');
const imageInput = document.getElementById('image-input');
const imagePreviewContainer = document.querySelector('.image-preview-container');
const imagePreview = document.getElementById('image-preview');
const removeImageBtn = document.getElementById('remove-image');
const loadingIndicator = document.querySelector('.loading-indicator');

// Global Variables
let selectedImage = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Hide the loading indicator on page load
    loadingIndicator.classList.add('hidden');
    
    // Set focus to the message input
    messageInput.focus();
    
    // Initialize the chat with welcome message
    displayWelcomeMessage();
    
    // Check connection to backend
    checkBackendConnection();
});

messageForm.addEventListener('submit', handleSubmit);
imageInput.addEventListener('change', handleImageSelection);
removeImageBtn.addEventListener('click', removeImage);
messageInput.addEventListener('input', validateInput);

// Functions
function displayWelcomeMessage() {
    const welcomeMessage = document.createElement('div');
    welcomeMessage.className = 'welcome-message';
    welcomeMessage.innerHTML = `
        <h2>Welcome to the STEM Learning Assistant!</h2>
        <p>I'm here to help you with your science, technology, engineering, and math questions. You can:</p>
        <ul>
            <li>Ask conceptual questions about STEM topics</li>
            <li>Get step-by-step solutions to problems</li>
            <li>Receive explanations of complex concepts</li>
            <li>Upload images of diagrams or handwritten problems</li>
        </ul>
        <p>Let's start learning together!</p>
    `;
    chatHistory.appendChild(welcomeMessage);
}

async function checkBackendConnection() {
    try {
        const response = await fetch('/api/health');
        if (!response.ok) {
            showError('Backend server is not responding properly. Check Vercel logs.');
        }
    } catch (error) {
        console.error('Backend connection error:', error);
        showError('Cannot connect to backend API. Check Vercel logs.');
    }
}

async function handleSubmit(event) {
    event.preventDefault();
    
    const userMessage = messageInput.value.trim();
    if (!userMessage && !selectedImage) {
        showError('Please enter a message or upload an image.');
        return;
    }
    
    addUserMessage(userMessage);
    showLoading('Thinking...');
    
    try {
        const requestData = {
            text_problem: userMessage || null,
            image_data: null
        };

        if (selectedImage) {
            const reader = new FileReader();
            reader.onloadend = async () => {
                const base64String = reader.result.split(',')[1];
                requestData.image_data = base64String;
                
                await makeApiCall(requestData);
            };
            reader.onerror = (error) => {
                console.error('Error reading image file:', error);
                showError('Failed to read the selected image file.');
                hideLoading();
            };
            reader.readAsDataURL(selectedImage);
        } else {
            await makeApiCall(requestData);
        }
        
    } catch (error) {
        console.error('Error in handleSubmit:', error);
        hideLoading();
        showError(error.message || 'Failed to get a response. Please try again.');
    }
    
    // Clear the input and image after sending
    messageInput.value = '';
    if (selectedImage) {
        removeImage();
    }
    
    // Re-validate the input field
    validateInput();
    
    // Focus back on the input field
    messageInput.focus();
}

async function makeApiCall(requestData) {
    try {
        const response = await fetch('/api/solve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();

        if (!response.ok) {
            const errorMessage = data.details || data.error || `Server error: ${response.status} ${response.statusText}`;
            throw new Error(errorMessage);
        }
        
        hideLoading();
        
        if (data.error) {
            showError(data.error + (data.details ? `: ${data.details}` : ''));
            return;
        }
        
        addBotMessage(data);

    } catch (error) {
        console.error('API call error:', error);
        hideLoading();
        showError(error.message || 'Failed to communicate with the server.');
        messageInput.value = '';
        if (selectedImage) removeImage();
        validateInput();
        messageInput.focus();
    }
}

function addUserMessage(message) {
    if (!message.trim()) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';
    messageElement.innerHTML = `<div class="message-content">${escapeHtml(message)}</div>`;
    
    // Add with animation
    messageElement.style.opacity = '0';
    messageElement.style.transform = 'translateY(20px)';
    chatHistory.appendChild(messageElement);
    
    // Force reflow
    messageElement.offsetHeight;
    
    // Animate in
    messageElement.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    messageElement.style.opacity = '1';
    messageElement.style.transform = 'translateY(0)';
    
    scrollToBottom();
}

function addBotMessage(data) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot-message';
    
    let innerHTML = '';
    
    if (data.solution) {
        innerHTML += `
            <div class="solution">
                <h3>Solution</h3>
                <div class="message-content">${advancedMarkdownToHtml(data.solution)}</div>
            </div>
        `;
    }
    
    if (data.explanation) {
        innerHTML += `
            <div class="explanation">
                <h3>Explanation</h3>
                <div class="message-content">${advancedMarkdownToHtml(data.explanation)}</div>
            </div>
        `;
    }
    
    if (data.practice_questions) {
        innerHTML += `
            <div class="practice-questions">
                <h3>Practice Questions</h3>
                <div class="message-content">${advancedMarkdownToHtml(data.practice_questions)}</div>
            </div>
        `;
    }
    
    // If there's just a simple response
    if (!data.solution && !data.explanation && !data.practice_questions && data.response) {
        innerHTML = `<div class="message-content">${advancedMarkdownToHtml(data.response)}</div>`;
    }
    
    // Add image if present
    if (data.image_url) {
        innerHTML += `<img src="${data.image_url}" alt="Response Image" class="message-image">`;
    }
    
    messageElement.innerHTML = innerHTML;
    
    // Add with animation
    messageElement.style.opacity = '0';
    messageElement.style.transform = 'translateY(20px)';
    chatHistory.appendChild(messageElement);
    
    // Force reflow
    messageElement.offsetHeight;
    
    // Animate in
    messageElement.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    messageElement.style.opacity = '1';
    messageElement.style.transform = 'translateY(0)';
    
    scrollToBottom();
    
    // Highlight code blocks using Prism.js if available
    if (window.Prism) {
        Prism.highlightAllUnder(messageElement);
    }
}

function advancedMarkdownToHtml(text) {
    if (!text) return '';
    
    // Escape HTML to prevent XSS
    let html = escapeHtml(text);
    
    // Convert code blocks
    html = html.replace(/```([a-z]*)\n([\s\S]*?)\n```/g, (match, language, code) => {
        const lang = language ? ` class="language-${language}"` : '';
        return `<pre><code${lang}>${code.trim()}</code></pre>`;
    });
    
    // Convert inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Convert bold text
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Convert italic text
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Convert unordered lists
    html = html.replace(/^\s*[-*+]\s+(.*?)(?=\n|$)/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*?<\/li>)\n(<li>)/g, '$1$2');
    html = html.replace(/(^|[^<])<li>/g, '$1<ul><li>');
    html = html.replace(/<\/li>(\n|$)(?![<\s]*<li>)/g, '</li></ul>');
    
    // Convert ordered lists
    html = html.replace(/^\s*(\d+)\.\s+(.*?)(?=\n|$)/gm, '<li>$2</li>');
    html = html.replace(/(?<!\n)<li>.*?<\/li>\n<li>/g, '<li>$&');
    html = html.replace(/(^|[^<])<li>/g, '$1<ol><li>');
    html = html.replace(/<\/li>(\n|$)(?![<\s]*<li>)/g, '</li></ol>');
    
    // Convert headings
    html = html.replace(/^###\s+(.*?)$/gm, '<h3>$1</h3>');
    html = html.replace(/^##\s+(.*?)$/gm, '<h2>$1</h2>');
    html = html.replace(/^#\s+(.*?)$/gm, '<h1>$1</h1>');
    
    // Convert paragraphs
    html = html.replace(/\n\n([\s\S]+?)(?=\n\n|$)/g, function(match, content) {
        // Don't wrap if already contains HTML tags
        if (
            content.trim().startsWith('<') || 
            content.includes('</') || 
            content.includes('<li>') || 
            content.includes('<code>')
        ) {
            return '\n\n' + content;
        }
        return '\n\n<p>' + content + '</p>';
    });
    
    // Remove unnecessary paragraph tags around HTML elements
    html = html.replace(/<p>(<(?:h[1-6]|ul|ol|pre|div|blockquote).*?<\/(?:h[1-6]|ul|ol|pre|div|blockquote)>)<\/p>/g, '$1');
    
    // Convert line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html.trim();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function handleImageSelection(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        showError('Please select an image file.');
        event.target.value = '';
        return;
    }
    
    selectedImage = file;
    const reader = new FileReader();
    
    reader.onload = function(e) {
        imagePreview.src = e.target.result;
        imagePreviewContainer.classList.remove('hidden');
        
        // Add animation
        imagePreviewContainer.style.animation = 'fadeIn 0.3s ease';
    };
    
    reader.readAsDataURL(file);
    validateInput();
}

function removeImage() {
    selectedImage = null;
    imageInput.value = '';
    imagePreviewContainer.classList.add('hidden');
    validateInput();
}

function validateInput() {
    if (messageInput.value.trim() || selectedImage) {
        submitBtn.disabled = false;
    } else {
        submitBtn.disabled = true;
    }
    
    // Auto-resize the textarea
    messageInput.style.height = 'auto';
    messageInput.style.height = (messageInput.scrollHeight) + 'px';
}

function showLoading(message = 'Processing...') {
    const loadingText = loadingIndicator.querySelector('p') || document.createElement('p');
    loadingText.textContent = message;
    
    if (!loadingIndicator.contains(loadingText)) {
        loadingIndicator.appendChild(loadingText);
    }
    
    loadingIndicator.classList.remove('hidden');
    submitBtn.disabled = true;
}

function hideLoading() {
    loadingIndicator.classList.add('hidden');
    validateInput();
}

function showError(message) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.textContent = message;
    
    // Add to DOM
    document.body.appendChild(toast);
    
    // Remove after animation completes
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function scrollToBottom() {
    // Smooth scroll to bottom
    chatHistory.scrollTo({
        top: chatHistory.scrollHeight,
        behavior: 'smooth'
    });
} 