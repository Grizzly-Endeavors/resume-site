document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const contentStream = document.getElementById('content-stream');
    const loadingIndicator = document.getElementById('loading-indicator');
    const chatSection = document.getElementById('chat-section');

    let visitorSummary = null;
    let previousBlockSummary = null;
    let isChatting = true;

    // --- Chat Logic ---

    function appendMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        div.textContent = text;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    async function sendChat(message) {
        if (!message) return;
        
        appendMessage(message, 'user');
        chatInput.value = '';
        chatInput.disabled = true;
        chatSend.disabled = true;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, visitor_context: {} })
            });
            const data = await res.json();

            if (data.ready) {
                // Transition to block generation
                visitorSummary = data.visitor_summary;
                isChatting = false;
                appendMessage("Thanks! Generating your personalized view...", 'ai');
                
                // Hide chat input after a delay or minimize it
                setTimeout(() => {
                    chatSection.classList.add('hidden'); // Or just minimize
                    startBlockGeneration();
                }, 1500);
            } else {
                appendMessage(data.message, 'ai');
                chatInput.disabled = false;
                chatSend.disabled = false;
                chatInput.focus();
            }
        } catch (err) {
            console.error(err);
            appendMessage("Sorry, I encountered an error.", 'ai');
            chatInput.disabled = false;
            chatSend.disabled = false;
        }
    }

    // Initial Greeting
    async function startChat() {
        chatInput.disabled = true;
        chatSend.disabled = true;
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: null }) // Trigger greeting
            });
            const data = await res.json();
            appendMessage(data.message, 'ai');
        } catch (err) {
            console.error(err);
        } finally {
            chatInput.disabled = false;
            chatSend.disabled = false;
        }
    }

    chatSend.addEventListener('click', () => sendChat(chatInput.value.trim()));
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChat(chatInput.value.trim());
    });

    // --- Block Generation Logic ---

    window.app = {
        handleAction: (type, value) => {
            generateBlock(type, value);
        }
    };

    async function startBlockGeneration() {
        await generateBlock('initial_load', null);
    }

    async function generateBlock(actionType, actionValue) {
        loadingIndicator.classList.remove('hidden');
        
        try {
            const res = await fetch('/api/generate-block', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    visitor_summary: visitorSummary,
                    previous_block_summary: previousBlockSummary,
                    action_type: actionType,
                    action_value: actionValue
                })
            });
            
            const data = await res.json();
            
            // Create wrapper for new block
            const wrapper = document.createElement('div');
            wrapper.innerHTML = data.html;
            
            // Execute scripts if any (innerHTML doesn't exec scripts by default)
            // But for safety/simplicity we rely on window.app.handleAction defined above
            // and inline onclick handlers which DO work with innerHTML in many cases 
            // OR we can explicitly eval script tags if we really need them.
            // The prompt asks for onclick="window.app.handleAction...", which works.
            
            contentStream.appendChild(wrapper);
            previousBlockSummary = data.block_summary;
            
            // Scroll to new block
            wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (err) {
            console.error(err);
            alert("Failed to load content.");
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    }

    // Start
    startChat();
});
