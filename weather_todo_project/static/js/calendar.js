// Calendar Module
class CalendarManager {
    constructor() {
        this.calendar = null;
        this.initCalendar();
    }

    initCalendar() {
        const calendarEl = document.getElementById('calendar');
        
        if (!calendarEl) return;

        this.calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: this.fetchEvents.bind(this),
            eventClick: (info) => {
                window.location.href = info.event.url;
            },
            dateClick: (info) => {
                this.showCreateTaskModal(info.dateStr);
            },
            eventDidMount: (info) => {
                // Add category class for styling
                const category = info.event.extendedProps.category;
                if (category) {
                    info.el.classList.add(category);
                }
                
                // Add tooltip
                const tooltip = document.createElement('div');
                tooltip.className = 'event-tooltip';
                tooltip.innerHTML = `
                    <strong>${info.event.title}</strong><br>
                    ${info.event.extendedProps.description || 'No description'}<br>
                    Status: ${info.event.extendedProps.status || 'N/A'}<br>
                    Priority: ${info.event.extendedProps.priority || 'N/A'}
                `;
                
                // Initialize Bootstrap tooltip
                new bootstrap.Tooltip(info.el, {
                    title: tooltip.innerHTML,
                    html: true,
                    placement: 'top'
                });
            },
            loading: (isLoading) => {
                if (isLoading) {
                    $('#calendar-loading').show();
                } else {
                    $('#calendar-loading').hide();
                }
            },
            eventColor: '#3788d8',
            eventTextColor: '#ffffff',
            height: 'auto',
            firstDay: 1, // Monday
            buttonText: {
                today: 'Today',
                month: 'Month',
                week: 'Week',
                day: 'Day'
            }
        });

        this.calendar.render();
        
        // Add navigation buttons
        this.addNavigationButtons();
    }

    fetchEvents(info, successCallback, failureCallback) {
        const start = info.start;
        
        $.ajax({
            url: '/todo/calendar/tasks/',
            method: 'GET',
            data: {
                year: start.getFullYear(),
                month: start.getMonth() + 1
            },
            success: (events) => {
                // Format events for FullCalendar
                const formattedEvents = events.map(event => ({
                    id: event.id,
                    title: event.title,
                    start: event.start,
                    end: event.start,
                    allDay: true,
                    description: event.description,
                    category: event.category,
                    status: event.status,
                    priority: event.priority,
                    url: event.url,
                    backgroundColor: this.getCategoryColor(event.category),
                    borderColor: this.getCategoryColor(event.category),
                    textColor: '#ffffff'
                }));
                
                successCallback(formattedEvents);
            },
            error: (xhr) => {
                failureCallback();
                this.showNotification('Error loading calendar events', 'danger');
            }
        });
    }

    getCategoryColor(category) {
        const colors = {
            'work': '#3498db',
            'personal': '#2ecc71',
            'shopping': '#f39c12',
            'business': '#9b59b6',
            'wishlist': '#e74c3c',
            'uncategorized': '#95a5a6'
        };
        
        return colors[category] || colors.uncategorized;
    }

    showCreateTaskModal(date) {
        // Show modal to create task for selected date
        $('#taskDate').val(date);
        $('#createTaskModal').modal('show');
    }

    addNavigationButtons() {
        // Add custom buttons if needed
        $('.fc-toolbar').append(`
            <button class="btn btn-sm btn-outline-primary ms-2" onclick="calendarManager.refreshCalendar()">
                <i class="fas fa-sync-alt"></i> Refresh
            </button>
        `);
    }

    refreshCalendar() {
        this.calendar.refetchEvents();
        this.showNotification('Calendar refreshed', 'info');
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

// Initialize calendar when document is ready
$(document).ready(function() {
    if (document.getElementById('calendar')) {
        window.calendarManager = new CalendarManager();
    }
});