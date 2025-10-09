// Weekly Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Apply responsive class
    const gridElement = document.querySelector('[style*="grid-template-columns: auto 1fr auto"]');
    if (gridElement) {
        gridElement.classList.add('grid-layout-compact');
    }
    
    let currentMonth = parseInt(document.querySelector('#calendar-month')?.dataset?.month || new Date().getMonth());
    let currentYear = parseInt(document.querySelector('#calendar-month')?.dataset?.year || new Date().getFullYear());
    
    // Month navigation
    window.changeMonth = function(direction) {
        currentMonth += direction;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        } else if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        
        // Update calendar via AJAX
        fetch(`/get-calendar-data/?month=${currentMonth + 1}&year=${currentYear}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('calendar-month').innerHTML = data.month_name;
                document.getElementById('calendar-grid').innerHTML = data.calendar_html;
            })
            .catch(error => console.error('Error:', error));
    };
    
    // Show day entry
    window.showDayEntry = function(date) {
        fetch(`/get-day-entry/?date=${date}`)
            .then(response => response.json())
            .then(data => {
                if (data.entry) {
                    // Create and show modal with entry details
                    const modal = document.createElement('div');
                    modal.style.cssText = `
                        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                        background: rgba(0,0,0,0.7); z-index: 1000;
                        display: flex; align-items: center; justify-content: center;
                        padding: 20px;
                    `;
                    
                    modal.innerHTML = `
                        <div style="
                            background: white; border-radius: 15px; padding: 25px;
                            max-width: 500px; width: 100%; max-height: 80vh; overflow-y: auto;
                            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                <h3 style="margin: 0; color: #333;">📅 ${data.entry.date}</h3>
                                <button onclick="this.closest('[style*=fixed]').remove()" style="
                                    background: none; border: none; font-size: 24px;
                                    cursor: pointer; color: #666; padding: 5px;
                                ">×</button>
                            </div>
                            <div style="color: #333;">
                                <h4 style="color: #667eea; margin-bottom: 10px;">🎉 ${data.entry.title}</h4>
                                <p style="margin-bottom: 15px;">${data.entry.description}</p>
                                ${data.entry.mood_rating ? `<div style="margin-bottom: 10px;"><strong>Mood:</strong> ${data.entry.mood_rating}/10</div>` : ''}
                                ${data.entry.category ? `<div style="margin-bottom: 10px;"><strong>Category:</strong> ${data.entry.category}</div>` : ''}
                                <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; font-size: 0.9rem; color: #666;">
                                    Created: ${data.entry.created_at}
                                </div>
                            </div>
                        </div>
                    `;
                    
                    document.body.appendChild(modal);
                    
                    // Close modal when clicking outside
                    modal.addEventListener('click', (e) => {
                        if (e.target === modal) modal.remove();
                    });
                }
            })
            .catch(error => console.error('Error:', error));
    };
    
    // Sticky Notes Functions
    window.createFirstNote = function(element) {
        element.focus();
        element.addEventListener('blur', function() {
            const content = this.textContent.trim();
            if (content) {
                createStickyNote(content, this);
            }
        });
        
        element.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur();
            }
        });
    };
    
    function createStickyNote(content, element) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) {
            console.error('CSRF token not found');
            return;
        }
        
        fetch('/sticky-notes/create/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `content=${encodeURIComponent(content)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Replace the placeholder with real note
                const noteElement = element.closest('.sticky-note');
                noteElement.setAttribute('data-note-id', data.note.id);
                noteElement.innerHTML = `
                    <div class="sticky-note-content" contenteditable="true">${data.note.content}</div>
                    <div class="sticky-note-actions">
                        <button class="complete-btn" title="Complete as win" onclick="completeNote(${data.note.id})">✓</button>
                        <button class="delete-btn" title="Delete note" onclick="deleteNote(${data.note.id})">×</button>
                    </div>
                `;
                
                // Add the + button if it doesn't exist
                if (!document.getElementById('add-note-btn')) {
                    const addButton = document.createElement('button');
                    addButton.id = 'add-note-btn';
                    addButton.className = 'add-note-button';
                    addButton.onclick = addNewNote;
                    addButton.title = 'Add another note';
                    addButton.textContent = '+';
                    document.getElementById('sticky-notes-container').appendChild(addButton);
                }
                
                setupNoteEditing(noteElement);
            }
        })
        .catch(error => console.error('Error:', error));
    }
    
    window.addNewNote = function() {
        const container = document.getElementById('sticky-notes-container');
        const addBtn = document.getElementById('add-note-btn');
        
        // Check if we already have 6 notes (max limit)
        const existingNotes = container.querySelectorAll('.sticky-note').length;
        if (existingNotes >= 6) {
            alert('Maximum 6 notes allowed. Complete or delete some notes to add more!');
            return;
        }
        
        const newNote = document.createElement('div');
        newNote.className = 'sticky-note';
        newNote.setAttribute('data-note-id', 'new');
        newNote.innerHTML = `
            <div class="sticky-note-content" contenteditable="true" data-placeholder="Quick note..."></div>
        `;
        
        container.insertBefore(newNote, addBtn);
        
        const contentDiv = newNote.querySelector('.sticky-note-content');
        contentDiv.focus();
        
        contentDiv.addEventListener('blur', function() {
            const content = this.textContent.trim();
            if (content) {
                createStickyNote(content, this);
            } else {
                newNote.remove();
            }
        });
        
        contentDiv.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur();
            }
        });
    };
    
    function setupNoteEditing(noteElement) {
        const contentDiv = noteElement.querySelector('.sticky-note-content');
        const noteId = noteElement.getAttribute('data-note-id');
        
        contentDiv.addEventListener('blur', function() {
            const content = this.textContent.trim();
            updateStickyNote(noteId, content);
        });
        
        contentDiv.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur();
            }
        });
    }
    
    function updateStickyNote(noteId, content) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) return;
        
        fetch(`/sticky-notes/${noteId}/update/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `content=${encodeURIComponent(content)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.deleted) {
                // Note was deleted because content was empty
                document.querySelector(`[data-note-id="${noteId}"]`).remove();
            }
        })
        .catch(error => console.error('Error:', error));
    }
    
    window.completeNote = function(noteId) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) return;
        
        fetch(`/sticky-notes/${noteId}/complete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Celebration animation
                const noteElement = document.querySelector(`[data-note-id="${noteId}"]`);
                noteElement.style.transform = 'scale(1.2) rotate(0deg)';
                noteElement.style.background = '#4caf50';
                noteElement.style.color = 'white';
                
                setTimeout(() => {
                    noteElement.style.transition = 'all 0.5s ease-out';
                    noteElement.style.transform = 'scale(0) rotate(180deg)';
                    noteElement.style.opacity = '0';
                    
                    setTimeout(() => {
                        noteElement.remove();
                        showCelebration(`🎉 "${data.entry.title}" added to your wins!`);
                        // Reload page to show the new entry
                        location.reload();
                    }, 500);
                }, 300);
            }
        })
        .catch(error => console.error('Error:', error));
    };
    
    window.deleteNote = function(noteId) {
        // Create custom delete modal
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.2s ease;
        `;
        
        modal.innerHTML = `
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes slideUp {
                    from {
                        transform: translateY(20px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
            </style>
            <div style="
                background: white;
                border-radius: 12px;
                padding: 24px;
                max-width: 400px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                animation: slideUp 0.3s ease;
            ">
                <h3 style="margin: 0 0 12px 0; color: #333; font-size: 20px;">Delete note?</h3>
                <p style="margin: 0 0 24px 0; color: #666; line-height: 1.5;">This action cannot be undone.</p>
                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button onclick="this.closest('[data-modal]').remove()" style="
                        padding: 10px 20px;
                        border: 1px solid #ddd;
                        background: white;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 14px;
                        color: #333;
                        transition: all 0.2s;
                    " onmouseover="this.style.background='#f5f5f5'" onmouseout="this.style.background='white'">
                        Cancel
                    </button>
                    <button onclick="window.confirmDeleteNote(${noteId})" style="
                        padding: 10px 20px;
                        border: none;
                        background: #dc3545;
                        color: white;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: all 0.2s;
                    " onmouseover="this.style.background='#c82333'" onmouseout="this.style.background='#dc3545'">
                        Delete
                    </button>
                </div>
            </div>
        `;
        
        modal.setAttribute('data-modal', 'true');
        document.body.appendChild(modal);
    };
    
    window.confirmDeleteNote = function(noteId) {
        // Remove modal
        document.querySelector('[data-modal]')?.remove();
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) return;
        
        // Proceed with deletion
        fetch(`/sticky-notes/${noteId}/delete/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const noteElement = document.querySelector(`[data-note-id="${noteId}"]`);
                noteElement.style.transition = 'all 0.3s ease-out';
                noteElement.style.transform = 'scale(0) rotate(-10deg)';
                noteElement.style.opacity = '0';
                
                setTimeout(() => noteElement.remove(), 300);
            }
        })
        .catch(error => console.error('Error:', error));
    };
    
    function showCelebration(message) {
        const celebration = document.createElement('div');
        celebration.style.cssText = `
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: #4caf50; color: white; padding: 20px 30px;
            border-radius: 10px; font-size: 1.1rem; font-weight: bold;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3); z-index: 2000;
            animation: celebrationBounce 0.6s ease-out;
        `;
        celebration.textContent = message;
        document.body.appendChild(celebration);
        
        setTimeout(() => celebration.remove(), 3000);
    }
    
    // Note: loadEntryModal and form submission are handled in the template
    // (weekly_dashboard.html) to avoid conflicts
    
    window.deleteEntry = function(entryId) {
        if (confirm('Are you sure you want to delete this entry? This action cannot be undone.')) {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (!csrfToken) return;
            
            fetch(`/entry/${entryId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Refresh the page
                    window.location.reload();
                } else {
                    alert('Error deleting entry. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error deleting entry. Please try again.');
            });
        }
    };
    
    // Handle day card clicks
    document.querySelectorAll('.day-card-clickable').forEach(dayCard => {
        dayCard.addEventListener('click', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.entry-actions') || e.target.closest('button')) {
                return;
            }
            
            const date = this.dataset.date;
            loadEntryModal(date);
        });
        
        // Show action buttons on hover
        dayCard.addEventListener('mouseenter', function() {
            const actions = this.querySelector('.entry-actions');
            if (actions) {
                actions.style.opacity = '1';
            }
        });
        
        dayCard.addEventListener('mouseleave', function() {
            const actions = this.querySelector('.entry-actions');
            if (actions) {
                actions.style.opacity = '0';
            }
        });
    });
    
    // Initialize existing note editing
    document.querySelectorAll('.sticky-note[data-note-id]:not([data-note-id="new"])').forEach(setupNoteEditing);
    
    // Add celebration animation CSS
    if (!document.getElementById('celebration-styles')) {
        const style = document.createElement('style');
        style.id = 'celebration-styles';
        style.textContent = `
            @keyframes celebrationBounce {
                0% { transform: translate(-50%, -50%) scale(0); }
                50% { transform: translate(-50%, -50%) scale(1.1); }
                100% { transform: translate(-50%, -50%) scale(1); }
            }
        `;
        document.head.appendChild(style);
    }
});