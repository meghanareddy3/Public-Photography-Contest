// frontend/script.js

document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.getElementById('signup-form');
    const message = document.getElementById('message');

    signupForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // Prevent the form from submitting

        const formData = new FormData(signupForm); // Get form data
        const userData = {
            email: formData.get('email'),
            password: formData.get('password')
        };

        try {
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (response.ok) {
                message.textContent = data.message;
            } else {
                message.textContent = data.message || 'Signup failed';
            }
        } catch (error) {
            console.error('Error:', error);
            message.textContent = 'An error occurred while signing up';
        }
    });
});
