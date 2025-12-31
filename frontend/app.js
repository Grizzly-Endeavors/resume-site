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
    const disclaimerContactWrapper = document.querySelector('.disclaimer-contact-wrapper');

    // Check if essential elements are found
    if (!loadingIndicator) console.error('loadingIndicator not found');
    if (!aiDisclaimer) console.error('aiDisclaimer not found');
    if (!contentStream) console.error('contentStream not found');
    if (!chatHistory) console.error('chatHistory not found');
    if (!chatInput) console.error('chatInput not found');
    if (!chatSend) console.error('chatSend not found');
    if (!chatSection) console.error('chatSection not found');
    if (!bottomChatbar) console.error('bottomChatbar not found');
    if (!chatbarInput) console.error('chatbarInput not found');
    if (!chatbarSend) console.error('chatbarSend not found');
    if (!suggestedButtons) console.error('suggestedButtons not found');
    if (!disclaimerContactWrapper) console.error('disclaimerContactWrapper not found');

    let visitorSummary = null;
    let isChatting = true;
    let chatHistoryData = []; // Stores {role: 'user'|'ai', content: string}
    let blockDataMap = new Map(); // Maps block ID to {actionType, actionValue, blockSummary}

    // Context Tracker
    let contextTracker = {
        blockSummaries: [],
        shownExperienceCounts: {}
    };

    // --- Chat Logic ---

    function appendMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        div.textContent = text;

        // Use requestAnimationFrame for smooth rendering
        requestAnimationFrame(() => {
            chatHistory.appendChild(div);
        });

        chatHistoryData.push({ role: sender === 'user' ? 'user' : 'assistant', content: text });
    }

    async function sendChat(message) {
        if (!message && chatHistoryData.length > 0) return; 
        
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
                visitorSummary = data.visitor_summary;
                isChatting = false;
                appendMessage("Thanks! Generating your personalized view...", 'ai');
                
                setTimeout(() => {
                    chatSection.classList.add('hidden'); 
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
        await generateBlock('initial_load', null);

        if (bottomChatbar) bottomChatbar.classList.remove('hidden');
        if (disclaimerContactWrapper) disclaimerContactWrapper.classList.remove('hidden');
        console.log('Bottom chatbar and disclaimer-contact-wrapper shown');

        await loadSuggestedButtons();
    }

    async function generateBlock(actionType, actionValue, blockId = null) {
        if (!loadingIndicator || !aiDisclaimer || !contentStream || !disclaimerContactWrapper) {
            console.error('Required DOM elements not found');
            return;
        }

        // Apply slide-down animation to disclaimer-contact-wrapper when loading new content
        if (!blockId) {
            // Slide down the wrapper to make room for spinner
            disclaimerContactWrapper.classList.add('slide-down');
        }

        // Show loading indicator with a smooth fade-in transition
        loadingIndicator.classList.remove('hidden');

        // Scroll loading indicator into view
        setTimeout(() => {
            if (loadingIndicator) loadingIndicator.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);

        try {
            // Build context object
            const context = {
                block_summaries: contextTracker.blockSummaries,
                shown_experience_counts: contextTracker.shownExperienceCounts
            };

            const res = await fetch('/api/generate-block', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    visitor_summary: visitorSummary,
                    context: context,
                    action_type: actionType,
                    action_value: actionValue
                })
            });

            const data = await res.json();

            // Update context tracker
            contextTracker.blockSummaries.push(data.block_summary);

            if (data.experience_ids) {
                data.experience_ids.forEach(id => {
                    contextTracker.shownExperienceCounts[id] = (contextTracker.shownExperienceCounts[id] || 0) + 1;
                });
            }

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

            // Extract scripts from HTML before injection
            // (scripts in innerHTML don't execute, so we need to extract and append them separately)
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = data.html;
            const scripts = Array.from(tempDiv.querySelectorAll('script'));

            // Remove script tags from HTML to inject
            const htmlWithoutScripts = data.html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');

            // Set wrapper content (without scripts)
            wrapper.innerHTML = htmlWithoutScripts;

            // Execute extracted scripts
            // Scripts appended to DOM after elements are in place will execute properly
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                if (script.src) {
                    newScript.src = script.src;
                } else {
                    newScript.textContent = script.textContent;
                }
                wrapper.appendChild(newScript);
            });

            // Add regenerate button
            const regenerateBtn = document.createElement('button');
            regenerateBtn.className = 'regenerate-btn';
            regenerateBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
            </svg>`;
            regenerateBtn.title = 'Regenerate this block';
            regenerateBtn.onclick = () => regenerateBlock(newBlockId);

            wrapper.appendChild(regenerateBtn);

            if (blockId) {
                const existingBlock = document.getElementById(blockId);
                if (existingBlock) {
                    existingBlock.replaceWith(wrapper);
                }
            } else {
                contentStream.appendChild(wrapper);

                // Remove slide-down animation class after content is added
                if (disclaimerContactWrapper) disclaimerContactWrapper.classList.remove('slide-down');
            }

            // Scroll smoothly to the new block
            wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // Load suggested buttons while keeping loading indicator briefly visible for consistency
            await loadSuggestedButtons();

        } catch (err) {
            console.error(err);
            alert("Failed to load content.");
        } finally {
            // Hide loading indicator
            if (loadingIndicator) loadingIndicator.classList.add('hidden');
        }
    }

    function extractTopicFromSummary(summary) {
        if (!summary) return null;
        const match = summary.match(/(?:Explored|Displayed|Showed|Highlighted)\s+(.+?)(?:\s+at|\s+from|\s+in|$)/i);
        if (match && match[1]) {
            return match[1].trim();
        }
        return summary.substring(0, 50).trim();
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

            // Build context object
            const context = {
                block_summaries: contextTracker.blockSummaries,
                shown_experience_counts: contextTracker.shownExperienceCounts
            };

            const res = await fetch('/api/generate-buttons', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    visitor_summary: visitorSummary,
                    chat_history: chatHistoryData,
                    context: context
                })
            });

            const data = await res.json();
            console.log('Received buttons:', data);

            suggestedButtons.innerHTML = '';

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

        chatHistoryData.push({ role: 'user', content: message });

        await generateBlock('user_question', message);

        chatbarInput.disabled = false;
        chatbarSend.disabled = false;
        chatbarInput.focus();
    }

    chatbarSend.addEventListener('click', () => handleChatbarMessage(chatbarInput.value.trim()));
    chatbarInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleChatbarMessage(chatbarInput.value.trim());
    });

    startChat();
});