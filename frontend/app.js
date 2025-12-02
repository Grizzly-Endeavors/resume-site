document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const contentStream = document.getElementById('content-stream');
    const loadingIndicator = document.getElementById('loading-indicator');
    const chatSection = document.getElementById('chat-section');
    const bottomChatbar = document.getElementById('bottom-chatbar');
    const chatbarInput = document.getElementById('chatbar-input');
    const chatbarSend = document.getElementById('chatbar-send');
    const suggestedButtons = document.getElementById('suggested-buttons');
    const aiDisclaimer = document.getElementById('ai-disclaimer');

    let visitorSummary = null;
    let previousBlockSummary = null;
    let isChatting = true;
    let chatHistoryData = []; // Stores {role: 'user'|'ai', content: string}
    let blockDataMap = new Map(); // Maps block ID to {actionType, actionValue, blockSummary}

    // --- Chat Logic ---

    function appendMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        div.textContent = text;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        
        // Add to history data
        // We map 'ai' in UI to 'assistant' for backend/LLM standard usually, 
        // but let's stick to what the backend expects. The backend likely wants 'user' and 'assistant' (or 'ai').
        // Let's use 'user' and 'model' or 'assistant'. 
        // For simplicity in this app, we'll store what we need.
        chatHistoryData.push({ role: sender === 'user' ? 'user' : 'assistant', content: text });
    }

    async function sendChat(message) {
        if (!message && chatHistoryData.length > 0) return; // Don't send empty if not start
        
        if (message) {
            appendMessage(message, 'user');
        }
        
        chatInput.value = '';
        chatInput.disabled = true;
        chatSend.disabled = true;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message, 
                    visitor_context: {},
                    history: chatHistoryData 
                })
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
                body: JSON.stringify({ 
                    message: null,
                    history: [] 
                }) 
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
        // Show the bottom chatbar and AI disclaimer
        bottomChatbar.classList.remove('hidden');
        aiDisclaimer.classList.remove('hidden');
        console.log('Bottom chatbar and AI disclaimer shown');

        await generateBlock('initial_load', null);
        await loadSuggestedButtons();
    }

    async function generateBlock(actionType, actionValue, blockId = null) {
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

            // Generate unique ID for this block
            const newBlockId = blockId || 'block-' + Date.now();

            // Store block data for regeneration
            blockDataMap.set(newBlockId, {
                actionType: actionType,
                actionValue: actionValue,
                blockSummary: data.block_summary
            });

            // Create wrapper for new block
            const wrapper = document.createElement('div');
            wrapper.className = 'block-wrapper';
            wrapper.id = newBlockId;

            // Set wrapper content
            wrapper.innerHTML = data.html;

            // Add regenerate button to wrapper (outside the resume-block)
            const regenerateBtn = document.createElement('button');
            regenerateBtn.className = 'regenerate-btn';
            regenerateBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
            </svg>`;
            regenerateBtn.title = 'Regenerate this block';
            regenerateBtn.onclick = () => regenerateBlock(newBlockId);

            wrapper.appendChild(regenerateBtn);

            if (blockId) {
                // Replace existing block
                const existingBlock = document.getElementById(blockId);
                if (existingBlock) {
                    existingBlock.replaceWith(wrapper);
                }
            } else {
                // Append new block
                contentStream.appendChild(wrapper);
                previousBlockSummary = data.block_summary;
            }

            // Scroll to block
            wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // Regenerate suggested buttons after each block
            await loadSuggestedButtons();

        } catch (err) {
            console.error(err);
            alert("Failed to load content.");
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    }

    async function regenerateBlock(blockId) {
        const blockData = blockDataMap.get(blockId);
        if (!blockData) {
            console.error('Block data not found for:', blockId);
            return;
        }

        const btn = document.querySelector(`#${blockId} .regenerate-btn`);
        if (btn) {
            btn.disabled = true;
            btn.classList.add('spinning');
        }

        try {
            await generateBlock(blockData.actionType, blockData.actionValue, blockId);
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.classList.remove('spinning');
            }
        }
    }

    // --- Bottom Chatbar Logic ---

    async function loadSuggestedButtons() {
        try {
            console.log('Loading suggested buttons...');
            const res = await fetch('/api/generate-buttons', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    visitor_summary: visitorSummary,
                    chat_history: chatHistoryData
                })
            });

            const data = await res.json();
            console.log('Received buttons:', data);

            // Clear existing buttons
            suggestedButtons.innerHTML = '';

            // Add new buttons
            data.buttons.forEach(btn => {
                const button = document.createElement('button');
                button.textContent = btn.label;
                button.onclick = () => handleChatbarMessage(btn.prompt);
                suggestedButtons.appendChild(button);
            });
            console.log(`Added ${data.buttons.length} buttons to the UI`);
        } catch (err) {
            console.error('Failed to load suggested buttons:', err);
        }
    }

    async function handleChatbarMessage(message) {
        if (!message.trim()) return;

        chatbarInput.value = '';
        chatbarInput.disabled = true;
        chatbarSend.disabled = true;

        // Add to chat history
        chatHistoryData.push({ role: 'user', content: message });

        // Generate a new block based on the message
        await generateBlock('user_question', message);

        chatbarInput.disabled = false;
        chatbarSend.disabled = false;
        chatbarInput.focus();
    }

    chatbarSend.addEventListener('click', () => handleChatbarMessage(chatbarInput.value.trim()));
    chatbarInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleChatbarMessage(chatbarInput.value.trim());
    });

    // Start
    startChat();
});
