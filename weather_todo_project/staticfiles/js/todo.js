// Todo Module
class TodoManager {
    constructor() {
        this.initEventListeners();
        this.initSelect2();
    }

    initEventListeners() {
        // Task completion toggle
        $(document).on('change', '.task-checkbox', (e) => {
            const taskId = $(e.target).data('task-id');
            this.toggleTaskStatus(taskId);
        });

        // Category filter
        $('#categoryFilter').on('change', () => {
            this.filterTasks();
        });

        // Status filter
        $('#statusFilter').on('change', () => {
            this.filterTasks();
        });

        // Search tasks
        $('#taskSearch').on('keyup', (e) => {
            this.searchTasks(e.target.value);
        });

        // Delete task confirmation
        $(document).on('click', '.delete-task', (e) => {
            if (!confirm('Are you sure you want to delete this task?')) {
                e.preventDefault();
            }
        });
    }

    initSelect2() {
        $('.select2').select2({
            placeholder: 'Select users to assign',
            allowClear: true
        });
    }

    toggleTaskStatus(taskId) {
        $.ajax({
            url: `/todo/task/${taskId}/toggle/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCsrfToken()
            },
            success: (response) => {
                const taskCard = $(`#task-${taskId}`);
                if (response.status === 'completed') {
                    taskCard.addClass('completed');
                    this.showNotification('Task completed! 🎉', 'success');
                    
                    // Add celebration effect
                    taskCard.effect('bounce', { times: 3 }, 300);
                } else {
                    taskCard.removeClass('completed');
                }
            },
            error: (xhr) => {
                const error = xhr.responseJSON?.error || 'Error updating task';
                this.showNotification(error, 'danger');
            }
        });
    }

    filterTasks() {
        const category = $('#categoryFilter').val();
        const status = $('#statusFilter').val();

        $('.task-card').each(function() {
            const taskCategory = $(this).data('category');
            const taskStatus = $(this).data('status');
            
            let show = true;
            
            if (category !== 'all' && taskCategory !== category) {
                show = false;
            }
            
            if (status !== 'all' && taskStatus !== status) {
                show = false;
            }
            
            if (show) {
                $(this).fadeIn(300);
            } else {
                $(this).fadeOut(300);
            }
        });
    }

    searchTasks(query) {
        query = query.toLowerCase();
        
        $('.task-card').each(function() {
            const title = $(this).find('.task-title').text().toLowerCase();
            const description = $(this).find('.task-description').text().toLowerCase();
            
            if (title.includes(query) || description.includes(query)) {
                $(this).fadeIn(300);
            } else {
                $(this).fadeOut(300);
            }
        });
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    showNotification(message, type) {
        const types = {
            'success': 'success',
            'danger': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        
        const toastClass = types[type] || 'info';
        
        const toast = $(`
            <div class="toast toast-${toastClass}" role="alert">
                <div class="toast-header">
                    <strong class="me-auto">
                        <i class="fas fa-${type === 'success' ? 'check-circle' : 
                                          type === 'danger' ? 'exclamation-circle' :
                                          type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
                        Notification
                    </strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `);

        $('.toast-container').append(toast);
        
        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast[0], { delay: 3000 });
        bsToast.show();

        // Remove from DOM after hiding
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
}

// Initialize todo manager when document is ready
$(document).ready(function() {
    window.todoManager = new TodoManager();
});