/* static/js/script.js */

document.addEventListener('DOMContentLoaded', () => {
    // Automatically close alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // Toggle menu item availability visually format (Staff dashboard)
    const toggleBtns = document.querySelectorAll('.toggle-availability');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const url = btn.dataset.url;
            const csrfCookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
            if (!csrfCookieMatch) return;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfCookieMatch[1],
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                const data = await response.json();
                if (data.success) {
                    const statusSpan = btn.parentElement.querySelector('.badge');
                    if (data.is_available) {
                        statusSpan.textContent = 'Available';
                        statusSpan.className = 'badge badge-success';
                        btn.textContent = 'Mark Unavailable';
                    } else {
                        statusSpan.textContent = 'Unavailable';
                        statusSpan.className = 'badge badge-danger';
                        btn.textContent = 'Mark Available';
                    }
                }
            } catch (err) {
                console.error('Error toggling availability', err);
            }
        });
    });
});
